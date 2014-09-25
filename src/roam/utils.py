import time
import logging
import os
import inspect
import sys
import getpass

from logging import handlers

from PyQt4 import uic
from PyQt4.QtGui import (QLabel, QDialog, QGridLayout, QLayout)

try:
   logpath = os.path.join(os.environ['ROAM_APPPATH'], 'log')
except KeyError:
   logpath = 'log' 

if not os.path.exists(logpath):
   os.makedirs(logpath)
LOG_FILENAME = os.path.join(logpath, "{}_roam.log".format(getpass.getuser()))
log_format = '%(levelname)s - %(asctime)s - %(module)s-%(funcName)s:%(lineno)d - %(message)s'
console_format = '%(levelname)s %(module)s-%(funcName)s:%(lineno)d - %(message)s'
formater = logging.Formatter(log_format)
console_formater = logging.Formatter(console_format)

filehandler = handlers.RotatingFileHandler(LOG_FILENAME, mode='at', maxBytes=1000000, backupCount=5)
filehandler.setLevel(logging.INFO)
filehandler.setFormatter(formater)

stream = logging.StreamHandler(stream=sys.stdout)
stream.setLevel(logging.DEBUG)
stream.setFormatter(console_formater)

logger = logging.getLogger("roam")
logger.addHandler(stream)
logger.addHandler(filehandler)
logger.setLevel(logging.DEBUG)

log = logger.debug
debug = logger.debug
info = logger.info 
warning = logger.warning
error = logger.error
critical = logger.critical
exception = logger.exception

uic.uiparser.logger.setLevel(logging.INFO)
uic.properties.logger.setLevel(logging.INFO)


class Timer():
    def __init__(self, message="", logging=log):
        self.message = message
        self.logging = logging

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        message = self.message + " " + str(time.time() - self.start)
        self.logging(message)


def timeit(method):
    def wrapper(*args, **kwargs):
        ts = time.time ()
        result = method(*args, **kwargs)
        th = time.time ()

        message = "%r %2.2f seconds " % (method.__name__, th-ts)
        info(message)
        return result
    return wrapper


def _pluralstring(text='', num=0):
    return "%d %s%s" % (num, text, "s"[num==1:])

