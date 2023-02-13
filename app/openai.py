import json
import os
import time
import requests
import uuid
from config import validation_sign, openai_endpoint, logger
from tenacity import retry, stop_after_attempt, wait_fixed



headers = {'Content-Type': 'application/json'}


### openai service
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def get_answer(msg, openid):
    data = {
        'sign': validation_sign,
        'text': msg,
        'openid': openid
    }
    url = openai_endpoint + '/api/chat'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code != 200 or response.content == '':
        err_msg = f'get_answer error: statuscode: {response.status_code}, {response.content}'
        logger.error(err_msg)
        raise Exception(err_msg)
    answer = str(response.content, encoding="utf-8")
    return answer


@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), reraise=True)
def text2speech(msg):
    data = {
        'sign': validation_sign,
        'text': msg,
        'voice': 'en-US-JaneNeural'
    }
    url = openai_endpoint + '/api/text2speech'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    if response.status_code != 200 :
        err_msg = f'text2speech error: statuscode: {response.status_code}, {response.content}'
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