import logging
import sys
import os
import getpass

try:
   logpath = os.path.join(os.environ['ROAM_APPPATH'], '_log')
except KeyError:
   #running from source
   logpath = '_log'
if not os.path.exists(logpath):
   os.makedirs(logpath)
LOG_FILENAME = os.path.join(logpath, "{}_configmanager.log".format(getpass.getuser()))

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

logger = logging.getLogger("configmanager")
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
