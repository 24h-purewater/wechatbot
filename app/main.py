from werobot import WeRoBot
from werobot.replies import VoiceReply

from openai import get_answer, text2speech_and_upload_media_to_wx
from bottle import Bottle
from werobot.contrib.bottle import make_view
from config import  token, port, app_id, app_secret, logger

robot = WeRoBot(token=token, APP_ID=app_id,
                APP_SECRET=app_secret)
client = robot.client
client.grant_token()


@robot.text
def echo(message):
    logger.info(f'userid:{message.source}, text content:{message.content}')
    answer = get_answer(message.content)
    return answer


@robot.voice
def echo(message):
    logger.info(f'from_user: {message.source}')
    recognition = message.recognition
    logger.info(f'userid:{message.source}, recognition:{recognition}')
    answer = get_answer(recognition)
    logger.info(f'userid:{message.source}, answer:{answer}')
    # answer to voice
    ret = text2speech_and_upload_media_to_wx(client, answer)
    logger.info(f'userid:{message.source}, upload ret:{ret}')
    if ret is not None:
        return VoiceReply(message=message, media_id=ret['media_id'])
    return None


app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

logger.info('server running at port %s', port)
app.run(host='0.0.0.0', port=port)
