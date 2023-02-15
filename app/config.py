import os
from dotenv import load_dotenv

from yaml import load, FullLoader


load_dotenv()

# openai_endpoint = os.getenv('OPENAI_ENDPOINT')
# validation_sign = os.getenv('VALIDATION_SIGN')
# app_id = os.getenv('APP_ID')
# app_secret = os.getenv('APP_SECRET')

# token = os.getenv("WX_TOKEN")
# port = os.getenv("PORT")
# wx_send_msg_buffer_period = os.getenv("WX_SEND_MSG_BUFFER_PERIOD", default=3)
# wx_welcome_msg = os.getenv("WX_WELCOME_MSG")
# multithreading = os.getenv("MULTITHREADING", default='off')


def get_yaml_config():
    config_path = os.getenv("CONFIG_PATH", default="/app/config.yaml")
    with open(config_path, 'r', encoding='UTF-8') as f:
        cfg = load(f, Loader=FullLoader)
    return cfg


cfg = get_yaml_config()

global_config = get_yaml_config()

ms = cfg.get('maintenance_status', True)

role = cfg.get('role', '')
maintenance_status = True if ms is None else ms
maintenance_msg = cfg.get('maintenance_msg')
slack_webhook = cfg.get('slack_webhook')
developer_open_id = cfg.get('developer_open_id')
open_ai_max_tokens = cfg.get('open_ai_max_tokens', 1000)
open_ai_fallback = cfg.get('open_ai_fallback', False)
wx_token = cfg.get('wx_token')
port = cfg.get('port')

log_level = cfg.get('log_level', 'info')
log_file = cfg.get('log_file', 'server.log')
openai_endpoint = cfg.get('openai_endpoint')
validation_sign = cfg.get('validation_sign')
app_id = cfg.get('app_id')
app_secret = cfg.get('app_secret')

multithreading = cfg.get('multithreading')
wx_send_msg_buffer_period = cfg.get('wx_send_msg_buffer_period')
wx_welcome_msg = cfg.get('wx_welcome_msg')