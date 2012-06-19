from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from ui_sync import Ui_syncForm
import os
import sys
from subprocess import Popen, PIPE

#This feels a bit hacky
pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pardir)

from utils import log

class Syncer(QObject):
    statusUpdate = pyqtSignal(bool, str)
    done = pyqtSignal()
    
    def doSync(self):
        curdir = os.path.abspath(os.path.dirname(__file__))
        cmdpath = os.path.join(curdir,'bin\SyncProofConcept.exe')
        p = Popen(cmdpath, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell = True)
        stdout, stderr = p.communicate()
        if not stdout == "":
            log(stdout)
            self.statusUpdate.emit(True, stdout)
        else:
            log(stderr)
            self.statusUpdate.emit(False, stderr)

class SyncDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_syncForm()
        self.ui.setupUi(self)
        self.ui.buttonBox.hide()
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = QApplication.desktop().screenGeometry(0)
        self.move( scr.center() - self.rect().center() )

    def updateStatus(self, state, text):
        if not state:
            self.ui.statusLabel.setStyleSheet("color: rgba(222, 13, 6);")
        self.ui.statusLabel.setText(text)
        self.ui.buttonBox.show()

    def runSync(self):
        self.syncer = Syncer()
        self.syncer.statusUpdate.connect(self.updateStatus)
        self.syncer.doSync()

if __name__ == "__main__":
    sync = Syncer()
    sync.doSync()