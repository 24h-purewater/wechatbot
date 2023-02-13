from werobot import WeRoBot

from openai import get_answer, text2speech_and_upload_media_to_wx
from bottle import Bottle
from werobot.contrib.bottle import make_view
from config import token, port, app_id, app_secret, logger, wx_send_msg_buffer_period
import queue
import threading
import time
robot = WeRoBot(token=token, APP_ID=app_id,
                APP_SECRET=app_secret)
client = robot.client


# worker queue
def consume_voice_msg(q):
    while True:
        try:
            message = q.get(block=True, timeout=1)
            recognition = message.recognition
            userid = message.source
            logger.info(f'userid:{userid} voice session start----------------------------------------------------------------')
            logger.info(f'userid:{userid}, recognition:{recognition}')
            answer = get_answer(recognition, userid)
            logger.info(f'userid:{userid}, answer:{answer}')
            if answer is None or answer == '':
                return None
            # answer to voice
            ret = text2speech_and_upload_media_to_wx(client, answer)
            logger.info(f'userid:{userid}, upload ret:{ret}')
            if ret is not None:
                time.sleep(int(wx_send_msg_buffer_period))
                send_ret = client.send_voice_message(userid, ret['media_id'])
                logger.info(f'userid:{userid}, send voice msg result:{send_ret}')
                if send_ret['errcode'] == 0:
                    # delete meterial
                    delete_ret = client.delete_permanent_media(ret['media_id'])
                    logger.info(f'userid:{userid}, delete media result:{delete_ret}')
            logger.info(f'userid:{userid} voice session end----------------------------------------------------------------')
            q.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f'consume voice msg error: {e}')


def consume_text_msg(q):
    while True:
        try:
            message = q.get(block=True, timeout=1)
            userid = message.source
            logger.info(f'userid:{userid} text session start----------------------------------------------------------------')
            logger.info(f'userid:{userid}, text content:{message.content}')
            answer = get_answer(message.content, userid)
            logger.info(f'userid:{userid}, answer:{answer}')
            send_ret = client.send_text_message(userid, answer)
            logger.info(f'userid:{userid}, send text msg result:{send_ret}')
            logger.info(f'userid:{userid} text session end----------------------------------------------------------------')
            q.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f'consume text msg error: {e}')


voice_queue = queue.Queue()
text_queue = queue.Queue()


voice_consumer_thread = threading.Thread(
    target=consume_voice_msg, args=(voice_queue,))
voice_consumer_thread.start()
text_consumer_thread = threading.Thread(
    target=consume_text_msg, args=(text_queue,))
text_consumer_thread.start()


# messsage handler
@robot.text
def handle_text_msg(message):
    text_queue.put(message)
    return None


@robot.voice
def handle_voice_msg(message):
    voice_queue.put(message)
    return None


# api server
app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

logger.info('server running at port %s', port)
app.run(host='0.0.0.0', port=port)