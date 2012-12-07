import time
from PyQt4 import uic
from qgis.core import QgsMessageLog
import logging
import os
from PyQt4.QtCore import QSettings

LOG_FILENAME = 'main.log'
uic.uiparser.logger.setLevel(logging.INFO)
uic.properties.logger.setLevel(logging.INFO)
logging.basicConfig(filename=LOG_FILENAME,level=logging.NOTSET)

log = lambda msg: logging.debug(msg)
info = lambda msg: logging.info(msg)
warning = lambda msg: logging.warning(msg)
error = lambda msg: logging.error(msg)

curdir = os.path.dirname(__file__)
settingspath = os.path.join(curdir,'settings.ini')
settings = QSettings(settingspath, QSettings.IniFormat)

class Timer():
    def __init__(self, message=""):
        self.message = message
    def __enter__(self):
        self.start = time.time()
    def __exit__(self, *args):
        log(self.message + " " + str(time.time() - self.start))

def timeit(method):
    def wrapper(*args, **kwargs):
        ts = time.time ()
        result = method (*args, **kwargs)
        th = time.time ()

       # log("% r (% r,% r)% 2.2f seconds " % (method.__name__, args, kw, th-ts))
        return result