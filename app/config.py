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




def get_logger():
    log_level = os.getenv("LOG_LEVEL")
    log_file = os.getenv("LOG_FILE")
    if log_level == "" or log_level is None:
        log_level = 'debug'

    if log_file == "" or log_file is None:
        log_file = 'server.log'    

    logger = Logger(log_file, level=log_level).logger
    return logger

logger = get_logger()