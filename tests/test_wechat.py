
from werobot import WeRoBot

from app.config import (app_id, app_secret, global_config, multithreading,
                        port, token, wx_send_msg_buffer_period, wx_welcome_msg)

robot = WeRoBot(token=token, APP_ID=app_id,
                APP_SECRET=app_secret)
client = robot.client


def test_upload_permanent_media():
    userid = global_config['developer_open_id']
    client.send_text_message(userid, 'test content')