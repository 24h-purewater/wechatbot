import json
import os
import time
import requests
import uuid
import re
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_fixed
from app.config import validation_sign, openai_endpoint, open_ai_max_tokens, mini_program_link
from app.log import logger
from app.constants import thinking_msg, reset_context_msg, default_error_msg, get_answer_timeout, mini_program_tip

headers = {'Content-Type': 'application/json'}


# openai service
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def get_answer_old(msg, openid):
    data = {
        'sign': validation_sign,
        'text': msg,
        'openid': openid,
        'maxTokens': open_ai_max_tokens
    }
    url = openai_endpoint + '/api/chat'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code != 200 or response.content == '':
        err_msg = f'get_answer error: url: {url}, statuscode: {response.status_code}, {response.content}, requestdata:{data}'
        logger.error(err_msg)
        raise Exception(err_msg)
    openaiCost = response.headers.get('X-Openai-Cost')
    logger.info(
        f'{openid} get_answer requestdata: {data}, response header X-Openai-Cost: {openaiCost}')
    answer = str(response.content, encoding="utf-8")
    return answer


@retry(stop=stop_after_delay(get_answer_timeout), wait=wait_fixed(1), reraise=True)
def get_answer(msg, openid):
    start = time.time()
    data = {
        'sign': validation_sign,
        'text': msg,
        'openid': openid,
        'maxTokens': open_ai_max_tokens
    }
    url = openai_endpoint + '/api/chat'
    response = requests.post(url=url, headers=headers,
                             data=json.dumps(data), timeout=get_answer_timeout)
    if response.status_code != 200 or response.content == '':
        err_msg = f'get_answer error: url: {url}, statuscode: {response.status_code}, {response.content}, requestdata:{data}'
        logger.error(err_msg)
        raise Exception(err_msg)
    openaiCost = response.headers.get('X-Openai-Cost')
    logger.info(
        f'{openid} get_answer requestdata: {data}, response header X-Openai-Cost: {openaiCost}')
    answer = str(response.content, encoding="utf-8")
    return answer if time.time()-start <= get_answer_timeout else None


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def reset_openai_context(openid):
    data = {
        'openid': openid,
    }
    url = openai_endpoint + '/api/resetContext'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code != 200 or response.content == '':
        err_msg = f'/api/resetContext error: url: {url}, statuscode: {response.status_code}, {response.content}, requestdata:{data}'
        logger.error(err_msg)
        raise Exception(err_msg)
    resp = str(response.content, encoding="utf-8")
    logger.info(f'{openid} resetContext requestdata: {data}, response: {resp}')
    return resp


def get_answer_from_context(openid, question):
    data = {
        'openid': openid,
    }
    url = openai_endpoint + '/api/currentContext'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    resp = str(response.content, encoding="utf-8")
    msg_list = resp.split('\n')
    for i, val in enumerate(msg_list):
        if val.find(question) >= 0:
            answer = msg_list[i+1]
            return answer.replace('AI:', '')
    return None


def get_answer_with_timeout(client, openid, msg):
    # request /api/currentContent 10 times to get answer
    for i in range(10):
        answer = get_answer_from_context(openid, msg)
        logger.info(
            f'{openid} request /api/currentContent to get answer({i}), result: {answer}')
        if answer is not None:
            return answer
        time.sleep(10)
    # after 10 times retry, if not get answer, then reset context, and send default msg
    reset_openai_context(openid)
    send_text_message(client, openid, reset_context_msg)
    time.sleep(5)
    send_text_message(client, openid, default_error_msg)
    return None


def get_answer_with_fallback(client, msg, openid):
    # loop = asyncio.get_event_loop()
    try:
        answer = get_answer(msg, openid)
        if answer is None:
            # if /api/chat request didn't get answer in 30s, start to request /api/currentContext
            # exec = loop.run_in_executor(None, lambda: send_timeout_message(client, openid))
            # exec.cancel()
            send_text_message(client, openid, thinking_msg)
            logger.info(
                f'{openid} request /api/chat did not get answer in {get_answer_timeout}s, start to request /api/currentContext')
            return get_answer_with_timeout(client, openid, msg)
        else:
            return answer
    except Exception as e:
        send_text_message(client, openid, thinking_msg)
        logger.info(f'{openid} get_answer_with_timeout_message error:{e}')
        return get_answer_with_timeout(client, openid, msg)


def contains_chinese(string):
    pattern = re.compile(r'[\u4e00-\u9fa5]+')
    match = pattern.search(string)
    return True if match else False


def contains_japanese(string):
    # 包含汉字： \u3040-\u30ff\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF
    # 不包含汉字： \u3040-\u309F\u30A0-\u30FF
    pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]+')
    match = pattern.search(string)
    return True if match else False


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def text2speech(openid, msg):
    if contains_japanese(msg):
        voice = 'ja-JP-MayuNeural'
    elif contains_chinese(msg):
        voice = 'zh-CN-XiaoxiaoNeural'
    else:
        voice = 'en-US-JaneNeural'
    data = {
        'sign': validation_sign,
        'text': msg,
        'voice': voice
    }
    url = openai_endpoint + '/api/text2speech'
    logger.info(f'{openid} text2speech: requestdata: {data}')
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        err_msg = f'{openid} text2speech error: url:{url}, statuscode: {response.status_code}, {response.content}, requestdata:{data}'
        logger.error(err_msg)
        raise Exception(err_msg)
    azureCost = response.headers.get('X-Azure-Cost')
    logger.info(
        f'{openid} text2speech response header X-Azure-Cost: {azureCost}')
    return response


# weixin
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def upload_permanent_media(client, file):
    try:
        upload_result = client.upload_permanent_media('voice', file)
        return upload_result
    except Exception as e:
        raise Exception(f'upload_permanent_media error: {e}')


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def upload_media(client, file):
    try:
        upload_result = client.upload_media('voice', file)
        return upload_result
    except Exception as e:
        raise Exception(f'upload_media error: {e}')


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def send_voice_message(client, userid, media_id):
    try:
        send_ret = client.send_voice_message(userid, media_id)
        logger.info(f'{userid} send voice msg result:{send_ret}')
        if send_ret['errcode'] != 0:
            raise Exception(f'send_voice_message error: {send_ret}')
        return send_ret
    except Exception as e:
        raise Exception(f'send_voice_message error: {e}')


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def send_text_message(client, userid, content):
    try:
        send_ret = client.send_text_message(userid, content)
        logger.info(f'{userid} send text msg result:{send_ret}')
        if send_ret['errcode'] != 0:
            raise Exception(f'send_text_message error: {send_ret}')
        return send_ret
    except Exception as e:
        raise Exception(f'send_text_message error: {e}')


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def send_miniprogram_info(client, userid):
    try:
        send_ret = client.send_text_message(userid, mini_program_tip)
        send_ret = client.send_text_message(userid, mini_program_link)
        logger.info(f'{userid} send text msg result:{send_ret}')
        if send_ret['errcode'] != 0:
            raise Exception(f'send_text_message error: {send_ret}')
        return send_ret
    except Exception as e:
        raise Exception(f'send_text_message error: {e}')


# service
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def text2speech_and_upload_media_to_wx(client, openid, msg):
    try:
        start = time.time()
        response = text2speech(openid, msg)
        if response.headers.get('Content-Length') == 0:
            return {'media_id': 'none', 'msg': msg}
        logger.info(f'{openid} text2speech_time: {time.time() - start}')
        # save response voice file
        filename = str(uuid.uuid4()) + '.mp3'
        open(filename, 'wb').write(response.content)
        file = open(filename, 'rb')
        # upload to wechat material
        try:
            upload_start = time.time()
            upload_result = upload_permanent_media(client, file)
            file.close()
            os.remove(filename)
            logger.info(
                f'{openid} upload_permanent_media_time: {time.time() - upload_start}')
            return upload_result
        except Exception as e:
            upload_start = time.time()
            logger.error(
                f'{openid} upload_permanent_media failed: {e}, switch to upload_media')
            upload_result = upload_media(client, file)
            file.close()
            os.remove(filename)
            logger.info(
                f'{openid} upload_media_time: {time.time() - upload_start}')
            return upload_result
    except Exception as e:
        logger.error(f'{openid} text2speech_and_upload_media_to_wx error: {e}')
        raise Exception(
            f'{openid} text2speech_and_upload_media_to_wx error: {e}')
