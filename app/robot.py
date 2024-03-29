import sys
from app.openai import (get_answer_old, get_answer_with_fallback,
                        send_text_message, send_voice_message,
                        text2speech_and_upload_media_to_wx, send_miniprogram_info)
from app.log import logger
from app.constants import default_error_msg
from app.config import (app_id, app_secret, developer_open_id, global_config,
                        maintenance_msg, maintenance_status, multithreading,
                        open_ai_fallback, port, wx_token,
                        wx_send_msg_buffer_period, wx_welcome_msg)
from werobot.contrib.bottle import make_view
from werobot import WeRoBot
from bottle import Bottle
import time
import threading



robot = WeRoBot(token=wx_token, APP_ID=app_id,
                APP_SECRET=app_secret)
client = robot.client


def on_voice_msg(message):
    userid = message.source
    recognition = message.recognition
    logger.info(
        f'{userid} voice session start----------------------------------------------------------------')
    logger.info(f'{userid} recognition:{recognition}')
    start_time = time.time()
    # get answer
    answer = default_error_msg
    if open_ai_fallback is True:
        answer = get_answer_with_fallback(client, recognition, userid)
        if answer is None:
            return
    else:
        answer = get_answer_old(recognition, userid)
    api_chat_time = time.time() - start_time
    logger.info(f'{userid} answer:{answer}')
    # answer to voice
    text2speech_start_time = time.time()
    ret = text2speech_and_upload_media_to_wx(client, userid, answer)
    text2speech_and_upload_time = time.time() - text2speech_start_time
    logger.info(f'{userid} upload ret:{ret}')
    if ret['media_id'] == 'none':
        direct_msg = ret['msg']
        logger.info(
            f'{userid} text2speech not success, maybe unknow language, send msg direct instead: {direct_msg}')
        send_text_message(client, userid, direct_msg)
        return
    if ret is not None:
        send_voice_msg_start_at = time.time()
        time.sleep(int(wx_send_msg_buffer_period))
        send_voice_message(client, userid, ret['media_id'])
        send_voice_msg_time = time.time() - send_voice_msg_start_at
        # delete meterial
        delete_ret = client.delete_permanent_media(ret['media_id'])
        logger.info(f'{userid} delete media result:{delete_ret}')
    logger.info(f'{userid} api_chat_time: {api_chat_time}, text2speech_and_upload_time: {text2speech_and_upload_time}, send_voice_msg_time: {send_voice_msg_time}, total_time: {time.time()-start_time}')
    return


def on_voice_msg_thread(message):
    try:
        on_voice_msg(message)
    except Exception as e:
        logger.error(f'on_voice_msg_thread error: {e}')
        send_miniprogram_info(client, message.source)


def on_text_msg(message):
    userid = message.source
    logger.info(
        f'{userid} text session start----------------------------------------------------------------')
    logger.info(f'{userid} text content:{message.content}')
    start_time = time.time()

    # get answer
    answer = default_error_msg
    if open_ai_fallback is True:
        answer = get_answer_with_fallback(client, message.content, userid)
        if answer is None:
            return
    else:
        answer = get_answer_old(message.content, userid)
    api_chat_time = time.time() - start_time
    logger.info(f'{userid} answer:{answer}')
    send_text_msg_start_at = time.time()
    send_text_message(client, userid, answer)
    send_text_msg_time = time.time() - send_text_msg_start_at
    logger.info(
        f'{userid} api_chat_time: {api_chat_time}, send_text_msg_time: {send_text_msg_time}, total_time: {time.time()-start_time}')
    return


def on_text_msg_thread(message):
    try:
        on_text_msg(message)
    except Exception as e:
        logger.error(f'on_text_msg_thread error: {e}')
        send_miniprogram_info(client, message.source)



# messsage handler
@robot.text
def handle_text_msg(message):
    if maintenance_status == True and message.source != developer_open_id:
        return maintenance_msg
    text_msg_thread = threading.Thread(
        target=on_text_msg_thread, args=(message,))
    text_msg_thread.start()
    return None


@robot.voice
def handle_voice_msg(message):
    if maintenance_status == True and message.source != developer_open_id:
        return maintenance_msg
    voice_msg_thread = threading.Thread(
        target=on_voice_msg_thread, args=(message,))
    voice_msg_thread.start()
    return None


def send_welcome_msg(client, userid):
    if len(wx_welcome_msg) > 0:
        msgstrList = wx_welcome_msg.split('|')
        for msgstr in msgstrList:
            if msgstr.startswith('text:'):
                send_text_message(client, userid, msgstr.replace('text:', ''))
            if msgstr.startswith('voice:'):
                send_voice_message(
                    client, userid, msgstr.replace('voice:', ''))
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
    logger.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception



def run():
    app = Bottle()
    app.route('/robot',
            ['GET', 'POST'],
            make_view(robot))

    logger.info('server running at port %s', port)
    logger.info(f'using config: {global_config}')
    access_token = client.get_access_token()
    logger.info(f'using access_token: {access_token}')
    app.run(host='0.0.0.0', port=port)