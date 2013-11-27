import time
import logging
import os
import json
import inspect
import yaml
import sys

from PyQt4 import uic
from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import (QLabel, QDialog, QGridLayout, QLayout)

uic.uiparser.logger.setLevel(logging.INFO)
uic.properties.logger.setLevel(logging.INFO)

LOG_FILENAME = 'roam.log'
log_format = '%(levelname)s - %(asctime)s - %(module)s-%(funcName)s:%(lineno)d - %(message)s'
console_format = '%(levelname)s %(module)s-%(funcName)s:%(lineno)d - %(message)s'
formater = logging.Formatter(log_format)
console_formater = logging.Formatter(console_format)

filehandler = logging.FileHandler('roam.log', mode='at')
filehandler.setLevel(logging.DEBUG)
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

curdir = os.getcwd()
settingspath = os.path.join(os.getcwd(), 'settings.config')


class Settings(dict):
    class Emitter(QObject):
        settings_changed = pyqtSignal()
        def __init__(self):
            super(Settings.Emitter, self).__init__()
        
    def __init__(self, path, *arg,**kwargs):
        super(Settings, self).__init__(*arg, **kwargs)
        self.settingspath = path
        self._emitter = Settings.Emitter()
        self.settings_changed = self._emitter.settings_changed
        
    def loadSettings(self): 
        with open(self.settingspath,'r') as f:
            settings = yaml.load(f)
            
    def saveSettings(self):
        with open(self.settingspath, 'w') as f:
            yaml.dump(data=self, stream=f, default_flow_style=False)
              
        self.settings_changed.emit()
      
settings_notify = Settings(settingspath)

with open(settingspath,'r') as f:
    settings = yaml.load(f)


def saveSettings():
    with open(settingspath, 'w') as f:
        yaml.dump(data=settings, stream=f, default_flow_style=False)
          
    settings_notify.settings_changed.emit()

appdata = os.path.join(os.environ['APPDATA'], "QMap")


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