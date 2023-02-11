import json
import requests
from config import validation_sign, openai_endpoint

headers = {'Content-Type': 'application/json'}

def get_answer(msg):
    data = {
        'sign': validation_sign,
        'text': msg
    }
    url = openai_endpoint + '/api/chat'
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    answer =  str(response.content , encoding = "utf-8")
    return answer