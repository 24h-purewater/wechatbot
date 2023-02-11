import os
from werobot import WeRoBot
from bottle import Bottle
from werobot.contrib.bottle import make_view
from dotenv import load_dotenv

from logger import get_logger


load_dotenv()
token = os.getenv("WX_TOKEN")
port = os.getenv("PORT")

logger = get_logger()

robot = WeRoBot(token=token)

@robot.handler
def hello(message):
    logger.info('message:',message)
    return 'Hello World!'

@robot.text
def echo(message):
    logger.info('text message:', message.content)
    return message.content


app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

app.run(host='0.0.0.0',port=port)