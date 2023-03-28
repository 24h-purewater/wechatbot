
from werobot import WeRoBot

from app.config import (app_id, app_secret, multithreading,
                        port, wx_token, wx_send_msg_buffer_period, wx_welcome_msg)
from app.openai import (get_answer_from_context, get_answer_with_fallback, send_miniprogram_info,
                        reset_openai_context)

test_open_id = 'obwgF6eYT_q-Wu6e_luvmZ9efb00'
robot = WeRoBot(token=wx_token, APP_ID=app_id,
                APP_SECRET=app_secret)

client = robot.client


def test_stop_tenacity():
    send_miniprogram_info(client, test_open_id)


# def test_get_answer_from_context():
#     s = get_answer_from_context('obwgF6eYT_q-Wu6e_luvmZ9efb00', '我听不懂日语')
#     print('answer',s)

# def test_reset_context():
#     s = reset_openai_context('obwgF6eYT_q-Wu6e_luvmZ9efb00')
#     print('answer', s)