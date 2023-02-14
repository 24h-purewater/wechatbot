import json
import logging
import os
from logging import handlers
from logging.handlers import HTTPHandler
from urllib.parse import urlparse

from slack_sdk.webhook import WebhookClient

from app.config import global_config


class SlackHandler(HTTPHandler):
    def __init__(self, url, username=None, icon_url=None, icon_emoji=None, channel=None, mention=None):
        o = urlparse(url)
        is_secure = o.scheme == 'https'
        HTTPHandler.__init__(self, o.netloc, o.path,
                             method="POST", secure=is_secure)
        self.username = username
        self.icon_url = icon_url
        self.icon_emoji = icon_emoji
        self.channel = channel
        self.mention = mention and mention.lstrip('@')

    def mapLogRecord(self, record):
        text = self.format(record)

        if isinstance(self.formatter, SlackFormatter):
            payload = {
                'attachments': [
                    text,
                ],
            }
            if self.mention:
                payload['text'] = '<@{0}>'.format(self.mention)
        else:
            if self.mention:
                text = '<@{0}> {1}'.format(self.mention, text)
            payload = {
                'text': text,
            }

        if self.username:
            payload['username'] = self.username
        if self.icon_url:
            payload['icon_url'] = self.icon_url
        if self.icon_emoji:
            payload['icon_emoji'] = self.icon_emoji
        if self.channel:
            payload['channel'] = self.channel

        ret = {
            'payload': json.dumps(payload),
        }
        return ret


class SlackFormatter(logging.Formatter):
    def format(self, record):
        ret = {}
        if record.levelname == 'INFO':
            ret['color'] = 'good'
        elif record.levelname == 'WARNING':
            ret['color'] = 'warning'
        elif record.levelname == 'ERROR':
            ret['color'] = '#E91E63'
        elif record.levelname == 'CRITICAL':
            ret['color'] = 'danger'

        ret['author_name'] = record.levelname
        ret['title'] = record.name
        ret['ts'] = record.created
        ret['text'] = super(SlackFormatter, self).format(record)
        return ret


class SlackLogFilter(logging.Filter):
    """
    Logging filter to decide when logging to Slack is requested, using
    the `extra` kwargs:
        `logger.info("...", extra={'notify_slack': True})`
    """

    def filter(self, record):
        return getattr(record, 'notify_slack', False)


class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }

    def __init__(self, filename, level='info', when='D', backCount=3, fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations.get(level))
        sh = logging.StreamHandler()
        sh.setFormatter(format_str)
        th = handlers.TimedRotatingFileHandler(
            filename=filename, when=when, backupCount=backCount, encoding='utf-8')
        th.setFormatter(format_str)
        self.logger.addHandler(sh)
        self.logger.addHandler(th)
        # slack logger
        sh = SlackHandler(username='logger', icon_emoji=':robot_face:',
                          url=global_config['slack_webhook'])
        sh.setLevel(logging.WARNING)

        f = SlackFormatter()
        sh.setFormatter(f)
        self.logger.addHandler(sh)


def get_logger():
    log_level = os.getenv("LOG_LEVEL", default="debug")
    log_file = os.getenv("LOG_FILE", default="server.log")
    logger = Logger(log_file, level=log_level).logger
    return logger


logger = get_logger()


def send_slack_webhook_msg():
    url = global_config['slack_webhook']
    webhook = WebhookClient(url)
    return webhook.send(
        text="fallback",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "You have a new request:\n*<fakeLink.toEmployeeProfile.com|Fred Enriquez - New device request>*"
                }
            }
        ]
    )
