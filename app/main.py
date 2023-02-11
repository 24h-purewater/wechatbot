from werobot import WeRoBot
from openai import get_answer
from bottle import Bottle
from werobot.contrib.bottle import make_view
from config import get_logger, token, port

logger = get_logger()

robot = WeRoBot(token=token)

@robot.handler
def hello(message):
    logger.info('message:',message)
    return 'Hello World!'

@robot.text
def echo(message):
    logger.info('text message:', message.content)
    answer = get_answer(message.content)
    return answer


app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

app.run(host='0.0.0.0',port=port)