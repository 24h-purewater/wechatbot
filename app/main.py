from werobot import WeRoBot

from openai import get_answer, text2speech_and_upload_media_to_wx
from bottle import Bottle
from werobot.contrib.bottle import make_view
from config import  token, port, app_id, app_secret, logger
import queue
import threading

robot = WeRoBot(token=token, APP_ID=app_id,
                APP_SECRET=app_secret)
client = robot.client


# worker queue
def consume_msg_event(q):
    while True:
        try:
            message = q.get(block=True, timeout=1)
            recognition = message.recognition
            logger.info(f'userid:{message.source}, recognition:{recognition}')
            answer = get_answer(recognition, message.source)
            logger.info(f'userid:{message.source}, answer:{answer}')
            if answer is None or answer == '':
                return None
            # answer to voice
            ret = text2speech_and_upload_media_to_wx(client, answer)
            logger.info(f'userid:{message.source}, upload ret:{ret}')
            if ret is not None:
                client.send_voice_message(message.source, ret['media_id'])
            q.task_done()
        except queue.Empty:
            continue
        except Exception as e: 
            logger.error(f'consume msg error: {e}')


q = queue.Queue()


consumer_thread = threading.Thread(target=consume_msg_event, args=(q,))
consumer_thread.start()



# messsage handler
@robot.text
def handle_text_msg(message):
    logger.info(f'userid:{message.source}, text content:{message.content}')
    answer = get_answer(message.content, message.source)
    return answer


@robot.voice
def handle_voice_msg(message):
    q.put(message)
    return None


# api server
app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

logger.info('server running at port %s', port)
app.run(host='0.0.0.0', port=port)