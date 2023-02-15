import os
from dotenv import load_dotenv

from yaml import load, FullLoader


load_dotenv()

openai_endpoint = os.getenv('OPENAI_ENDPOINT')
validation_sign = os.getenv('VALIDATION_SIGN')
app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

token = os.getenv("WX_TOKEN")
port = os.getenv("PORT")
wx_send_msg_buffer_period = os.getenv("WX_SEND_MSG_BUFFER_PERIOD", default=3)
wx_welcome_msg = os.getenv("WX_WELCOME_MSG")
multithreading = os.getenv("MULTITHREADING", default='off')


def get_yaml_config():
    config_path = os.getenv("CONFIG_PATH", default="/app/config.yaml")
    with open(config_path, 'r', encoding='UTF-8') as f:
        cfg = load(f, Loader=FullLoader)
    ms = cfg.get('maintenance_status', True)
    return {
        'role': cfg.get('role', ''),
        'maintenance_status': True if ms is None else ms,
        'maintenance_msg': cfg.get('maintenance_msg'),
        'slack_webhook': cfg.get('slack_webhook'),
        'developer_open_id': cfg.get('developer_open_id'),
        'open_ai_max_tokens': cfg.get('open_ai_max_tokens', 1000),
    }


global_config = get_yaml_config()