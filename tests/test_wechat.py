
from werobot import WeRoBot

from app.config import (app_id, app_secret, multithreading,
                        port, token, wx_send_msg_buffer_period, wx_welcome_msg)
from app.openai import (get_answer_from_context, get_answer_with_fallback,
                        reset_openai_context, stop)


def test_stop_tenacity():
    s = stop()
    print(s)



# def test_get_answer_from_context():
#     s = get_answer_from_context('obwgF6eYT_q-Wu6e_luvmZ9efb00', '我听不懂日语')
#     print('answer',s)

# def test_reset_context():
#     s = reset_openai_context('obwgF6eYT_q-Wu6e_luvmZ9efb00')
#     print('answer', s)