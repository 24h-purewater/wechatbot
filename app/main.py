from werobot import WeRoBot
from werobot.replies import VoiceReply

from openai import get_answer, text2speech_and_upload_media_to_wx
from bottle import Bottle
from werobot.contrib.bottle import make_view
from config import get_logger, token, port, app_id, app_secret

logger = get_logger()

robot = WeRoBot(token=token, APP_ID=app_id,
                APP_SECRET=app_secret)
client = robot.client
client.grant_token()


@robot.text
def echo(message):
    logger.info('text message:', message.content)
    answer = get_answer(message.content)
    return answer


@robot.voice
def echo(message):
    recognition = message.recognition
    answer = get_answer(recognition)
    # answer to voice
    ret = text2speech_and_upload_media_to_wx(answer)
    return VoiceReply(message=message, media_id=ret['media_id'])


app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

app.run(host='0.0.0.0', port=port)