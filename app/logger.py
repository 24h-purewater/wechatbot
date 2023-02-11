import logging
from logging import handlers
import os

class Logger(object):
    level_relations = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'crit':logging.CRITICAL
    }

    def __init__(self,filename,level='info',when='D',backCount=3,fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations.get(level))
        sh = logging.StreamHandler()
        sh.setFormatter(format_str) 
        th = handlers.TimedRotatingFileHandler(filename=filename,when=when,backupCount=backCount,encoding='utf-8')
        th.setFormatter(format_str)
        self.logger.addHandler(sh) 
        self.logger.addHandler(th)



def get_logger():
    log_level = os.getenv("LOG_LEVEL")
    log_file = os.getenv("LOG_FILE")

    if log_level == "" or log_file is None:
        log_level = 'debug'

    if log_file == "" or log_file is None:
        log_file = 'server.log'    

    logger = Logger(log_file, level=log_level).logger
    return logger