from app.config import get_yaml_config
from app.log import send_slack_webhook_msg, logger


def test_create_async_vector_env():
    config = get_yaml_config()
    print(config)


def test_slack_logger():
    logger.error('test error')
