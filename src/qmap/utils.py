import time
import logging
import os
import json
import inspect
import yaml

from PyQt4 import uic
from PyQt4.QtGui import (QLabel, QDialog, QGridLayout, QLayout)

LOG_FILENAME = 'main.log'
uic.uiparser.logger.setLevel(logging.INFO)
uic.properties.logger.setLevel(logging.INFO)
log_format = '%(asctime)s - %(module)s-%(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
logging.basicConfig(filename=LOG_FILENAME, filemode='at',level=logging.NOTSET, format=log_format)

logger = logging.getLogger("qmap")
log = logger.debug
info = logger.info 
warning = logger.warning
error = logger.error
critical = logger.critical

curdir = os.path.dirname(__file__)
settingspath = os.path.join(curdir,'..','settings.config')
with open(settingspath,'r') as f:
    settings = yaml.load(f)

appdata = os.path.join(os.environ['APPDATA'], "QMap")

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
    
def openImageViewer(pixmap):
        dlg = QDialog()
        dlg.setWindowTitle("Image Viewer")
        dlg.setLayout(QGridLayout())
        dlg.layout().setContentsMargins(0,0,0,0)
        dlg.layout().setSizeConstraint(QLayout.SetNoConstraint)
        dlg.resize(600,600)
        label = QLabel()
        label.mouseReleaseEvent = lambda x: dlg.accept()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        dlg.layout().addWidget(label)
        dlg.exec_()

def _pluralstring(text='', num=0):
    return "%d %s%s" % (num, text, "s"[num==1:])