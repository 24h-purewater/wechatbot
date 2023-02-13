import json
import os
import requests
import uuid
from config import validation_sign, openai_endpoint, logger

headers = {'Content-Type': 'application/json'}


def get_answer(msg, openid):
    data = {
        'sign': validation_sign,
        'text': msg,
        'openid': openid
    }
    url = openai_endpoint + '/api/chat'
    try:
        response = requests.post(url=url, headers=headers, data=json.dumps(data))
        answer = str(response.content, encoding="utf-8")
        return answer
    except Exception as e:
        logger.error(f'get_answer exception: {e}')
        return None



def text2speech_and_upload_media_to_wx(client, msg):
    data = {
        'sign': validation_sign,
        'text': msg,
        'voice': 'en-US-JaneNeural'
    }
    url = openai_endpoint + '/api/text2speech'
    try:
        response = requests.post(url=url, headers=headers, data=json.dumps(data))
        # save response voice file
        filename = str(uuid.uuid4()) + '.mp3'
        open(filename, 'wb').write(response.content)
        # upload to wechat material
        file = open(filename, 'rb')
        upload_result = upload_permanent_media(client, file)
        if upload_result is None:
            logger.info('upload_permanent_media failed, switch to upload_media')
            upload_result = upload_media(client, file)
        file.close()
        # delete tmp file
        os.remove(filename)
        return upload_result
    except Exception as e:
        logger.error(f'text2speech_and_upload_media_to_wx exception: {e}')
        return None



def upload_permanent_media(client, file):
    try:
        upload_result = client.upload_permanent_media('voice', file)
        return upload_result
    except Exception as e:
        logger.error(f'upload_permanent_media error: {e}')
        return None


def upload_media(client, file):
    try:
        upload_result = client.upload_media('voice', file)
        return upload_result
    except Exception as e:
        logger.error(f'upload_media error: {e}')
        return None        