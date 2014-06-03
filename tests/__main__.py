__author__ = 'nathan.woodrow'

import logging
import sys

def excepthook(errorhandler, exctype, value, traceback):
    errorhandler(exctype, value, traceback)
    logger.debug("Uncaught exception", exc_info=(exctype, value, traceback))

LOG_FILENAME = 'roam-tests.log'
log_format = '%(levelname)s - %(asctime)s - %(module)s-%(funcName)s:%(lineno)d - %(message)s'
console_format = '%(levelname)s %(module)s-%(funcName)s:%(lineno)d - %(message)s'
formater = logging.Formatter(log_format)
console_formater = logging.Formatter(console_format)

filehandler = logging.FileHandler(LOG_FILENAME, mode='at')
filehandler.setLevel(logging.DEBUG)
filehandler.setFormatter(formater)

stream = logging.StreamHandler(stream=sys.stdout)
stream.setLevel(logging.DEBUG)
stream.setFormatter(console_formater)

logger = logging.getLogger("roam")
logger.addHandler(filehandler)
logger.addHandler(stream)
logger.setLevel(logging.DEBUG)

sys.excepthook = excepthook

logger.info('Running Tests')
