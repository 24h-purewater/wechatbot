import sys

sys.path.append('..')
import queue
import threading
import time

from bottle import Bottle
from app.config import (app_id, app_secret, multithreading, port, token,
                    wx_send_msg_buffer_period, wx_welcome_msg, global_config)
from app.openai import (get_answer, send_text_message, send_voice_message,
                    text2speech_and_upload_media_to_wx)
from app.log import logger                    
from werobot import WeRoBot
from werobot.contrib.bottle import make_view

robot = WeRoBot(token=token, APP_ID=app_id,
                APP_SECRET=app_secret)
client = robot.client

default_error_msg = '系统繁忙，请稍后再试'


def on_voice_msg(message):
    userid = message.source
    recognition = message.recognition
    logger.info(f'userid:{userid} voice session start----------------------------------------------------------------')
    logger.info(f'userid:{userid}, recognition:{recognition}')
    start_time = time.time()
    answer = get_answer(recognition, userid)
    api_chat_time = time.time() - start_time
    logger.info(f'userid:{userid}, answer:{answer}')
    # answer to voice
    text2speech_start_time = time.time()
    ret = text2speech_and_upload_media_to_wx(client, answer)
    text2speech_and_upload_time = time.time() - text2speech_start_time
    logger.info(f'userid:{userid}, upload ret:{ret}')
    if ret['media_id'] == 'none':
        direct_msg = ret['msg']
        logger.info(f'userid:{userid}, text2speech not success, maybe unknow language, send msg direct instead: {direct_msg}')
        send_text_message(client, userid, direct_msg)
        return
    if ret is not None:
        send_voice_msg_start_at = time.time()
        time.sleep(int(wx_send_msg_buffer_period))
        send_voice_message(client, userid, ret['media_id'])
        send_voice_msg_time = time.time() - send_voice_msg_start_at
        # delete meterial
        delete_ret = client.delete_permanent_media(ret['media_id'])
        logger.info(f'userid:{userid}, delete media result:{delete_ret}')
    logger.info(f'''api_chat_time: {api_chat_time}, text2speech_and_upload_time: {text2speech_and_upload_time}, send_voice_msg_time: {send_voice_msg_time}, total_time: {time.time()-start_time}''')
    return

def on_voice_msg_thread(message):
    try:
        on_voice_msg(message)
    except Exception as e:
        logger.error(f'on_voice_msg_thread error: {e}')
        client.send_text_message(message.source, default_error_msg)

def on_text_msg(message):
    userid = message.source
    logger.info(f'userid:{userid} text session start----------------------------------------------------------------')
    logger.info(f'userid:{userid}, text content:{message.content}')
    start_time = time.time()
    answer = get_answer(message.content, userid)
    api_chat_time = time.time() - start_time
    logger.info(f'userid:{userid}, answer:{answer}')
    send_text_msg_start_at = time.time()
    send_text_message(client, userid, answer)
    send_text_msg_time = time.time() - send_text_msg_start_at
    logger.info(f'''api_chat_time: {api_chat_time}, send_text_msg_time: {send_text_msg_time}, total_time: {time.time()-start_time}''')
    return

def on_text_msg_thread(message):
    try:
        on_text_msg(message)
    except Exception as e:
        logger.error(f'on_text_msg_thread error: {e}')
        client.send_text_message(message.source, default_error_msg)



# worker queue
def consume_voice_msg(q):
    while True:
        try:
            message = q.get(block=True, timeout=0.5)
            on_voice_msg(message)
            q.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f'consume voice msg error: {e}')
            client.send_text_message(message.source, default_error_msg)


def consume_text_msg(q):
    while True:
        try:
            message = q.get(block=True, timeout=0.5)
            on_text_msg(message)
            q.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f'consume text msg error: {e}')
            client.send_text_message(message.source, default_error_msg) 


voice_queue = queue.Queue()
text_queue = queue.Queue()
if multithreading == 'off':
    voice_consumer_thread = threading.Thread(
        target=consume_voice_msg, args=(voice_queue,))
    voice_consumer_thread.start()
    text_consumer_thread = threading.Thread(
        target=consume_text_msg, args=(text_queue,))
    text_consumer_thread.start()


# messsage handler
@robot.text
def handle_text_msg(message):
    if global_config['maintenance_status'] == True and message.source != global_config['developer_open_id']:
        return global_config['maintenance_msg']
    if multithreading == 'on':
        text_msg_thread = threading.Thread(target=on_text_msg_thread, args=(message,))
        text_msg_thread.start()
        return None
    text_queue.put(message)
    return None


@robot.voice
def handle_voice_msg(message):
    if global_config['maintenance_status'] == True and message.source != global_config['developer_open_id']:
        return global_config['maintenance_msg']
    if multithreading == 'on':
        voice_msg_thread = threading.Thread(target=on_voice_msg_thread, args=(message,))
        voice_msg_thread.start()
        return None
    voice_queue.put(message)
    return None



def send_welcome_msg(client, userid):
    if len(wx_welcome_msg) > 0:
        msgstrList = wx_welcome_msg.split('|')
        for msgstr in msgstrList:
            if msgstr.startswith('text:'):
                send_text_message(client, userid, msgstr.replace('text:', '')) 
            if msgstr.startswith('voice:'):
                send_voice_message(client, userid, msgstr.replace('voice:', ''))
    return


@robot.subscribe
def subscribe(message):
    userid = message.source
    send_welcome_msg(client, userid)
    return None


# global error handler
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception




# api server
app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

logger.info('server running at port %s', port)
logger.info(f'using config: {global_config}')
access_token = client.get_access_token()
logger.info(f'using access_token: {access_token}')
app.run(host='0.0.0.0', port=port)