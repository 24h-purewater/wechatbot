import os
from werobot import WeRoBot
from bottle import Bottle
from werobot.contrib.bottle import make_view

import logging

token = os.getenv("WX_TOKEN")
port = os.getenv("PORT")
robot = WeRoBot(token=token)

@robot.handler
def hello(message):
    logging.info('message:',message)
    return 'Hello World!'


app = Bottle()
app.route('/robot',
          ['GET', 'POST'],
          make_view(robot))

app.run(host='0.0.0.0',port=port)