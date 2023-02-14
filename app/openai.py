import json
import os
import time
import requests
import uuid
import re
from tenacity import retry, stop_after_attempt, wait_fixed
from app.config import validation_sign, openai_endpoint, global_config
from app.log import logger

headers = {'Content-Type': 'application/json'}

openai_role = '''I want you to act as my teacher, we'll have daily conversation, here are the rules:
1.You reply to me in the language I use, so if I say Chinese to you, you reply to me in Chinese, if I say English to you you reply to me in English, if I say Japanese to you, you reply to me in Japanese
2.we ask and answer questions each other.
3.you must ask a new question when you answer.
4.the conversation must be helpful, creative, clever, and very friendly.
5.short sentences are preferred.
6.I want you to refuse any questions related to politics.
7.Your name is Scarlett Johansson
8.You don't want to talk about AI technology
'''



### openai service
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def get_answer(msg, openid):
    role = global_config['role']
    if role is None or role == '':
        role = openai_role
    data = {
        'sign': validation_sign,
        'text': msg,
        'openid': openid,
        'role': role
    }
    url = openai_endpoint + '/api/chat'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code != 200 or response.content == '':
        err_msg = f'get_answer error: url: {url}, statuscode: {response.status_code}, {response.content}, requestdata:{data}'
        logger.error(err_msg)
        raise Exception(err_msg)
    answer = str(response.content, encoding="utf-8")
    return answer


def contains_chinese(string):
    pattern = re.compile(r'[\u4e00-\u9fa5]+')
    match = pattern.search(string)
    return True if match else False

def contains_japanese(string):
    pattern = re.compile(r'[\u3040-\u30ff\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]+')
    match = pattern.search(string)
    return True if match else False

@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def text2speech(msg):
    if contains_japanese(msg):
        voice = 'ja-JP-MayuNeural'
    elif contains_chinese(msg):
        voice =  'zh-CN-XiaoxiaoNeural'
    else:
        voice = 'en-US-JaneNeural'
    data = {
        'sign': validation_sign,
        'text': msg,
        'voice': voice
    }
    url = openai_endpoint + '/api/text2speech'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code != 200 :
        err_msg = f'text2speech error: url:{url}, statuscode: {response.status_code}, {response.content}, requestdata:{data}'
        logger.error(err_msg)
        raise Exception(err_msg)
    return response


### weixin
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
        logger.info(f'userid:{userid}, send voice msg result:{send_ret}')
        if send_ret['errcode'] != 0:
            raise Exception(f'send_voice_message error: {send_ret}')
        return send_ret
    except Exception as e:
        raise Exception(f'send_voice_message error: {e}')



@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def send_text_message(client, userid, content):
    try:
        send_ret = client.send_text_message(userid, content)
        logger.info(f'userid:{userid}, send text msg result:{send_ret}')
        if send_ret['errcode'] != 0:
            raise Exception(f'send_text_message error: {send_ret}')
        return send_ret
    except Exception as e:
        raise Exception(f'send_text_message error: {e}')




# service
def text2speech_and_upload_media_to_wx(client, msg):
    try:
        start = time.time()
        response = text2speech(msg)
        if response.headers['Content-Length'] == 0:
            return {'media_id': 'none', 'msg': msg}
        logger.info(f'text2speech_time: {time.time() - start}')
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
            logger.info(f'upload_permanent_media_time: {time.time() - upload_start}')
            return upload_result
        except Exception as e:
            upload_start = time.time()
            logger.error(f'upload_permanent_media failed: {e}, switch to upload_media')
            upload_result = upload_media(client, file)
            file.close()
            os.remove(filename)
            logger.info(f'upload_media_time: {time.time() - upload_start}')
            return upload_result
    except Exception as e:
        raise Exception(f'text2speech_and_upload_media_to_wx error: {e}')