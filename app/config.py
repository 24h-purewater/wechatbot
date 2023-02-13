from logger import Logger
import os
from dotenv import load_dotenv

load_dotenv()

openai_endpoint = os.getenv('OPENAI_ENDPOINT')
validation_sign = os.getenv('VALIDATION_SIGN')
app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

token = os.getenv("WX_TOKEN")
port = os.getenv("PORT")
wx_send_msg_buffer_period = os.getenv("WX_SEND_MSG_BUFFER_PERIOD", default=3)


def get_logger():
    log_level = os.getenv("LOG_LEVEL", default="debug")
    log_file = os.getenv("LOG_FILE", default="server.log")
    logger = Logger(log_file, level=log_level).logger
    return logger

logger = get_logger()