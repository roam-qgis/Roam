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
    syncPass = pyqtSignal(str)
    syncFailed = pyqtSignal(str)
    
    def doSync(self):
        curdir = os.path.abspath(os.path.dirname(__file__))
        cmdpath = os.path.join(curdir,'bin\SyncProofConcept.exe')
        p = Popen(cmdpath, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell = True)
        stdout, stderr = p.communicate()
        if not stdout == "":
            log(stdout)
            self.syncPass.emit(stdout)
        else:
            log(stderr)
            self.syncFailed.emit(stderr)

class ImageSyncer(QObject):
    syncPass = pyqtSignal(str)
    syncFailed = pyqtSignal(str)
    
    def doSync(self):
        images = os.path.join(pardir, "data")
        server = "\\\\SD0302\\C$\\synctest\\"
        if not os.path.exists(images):
            return
        
        cmd = 'xcopy "%s" "%s" /Q /D /S /E /K /C /H /R /Y' % (images, server)
        print cmd
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell = True)
        stdout, stderr = p.communicate()
        if not stderr == "":
            self.syncFailed.emit(stderr)
        else:
            self.syncPass.emit(stdout)

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
        self.failed = False

    def updateStatus(self, text):
        self.ui.statusLabel.setText(text)
        self.ui.buttonBox.show()

    def updateFailedStatus(self, text):
        self.ui.statusLabel.setStyleSheet("color: rgba(222, 13, 6);")
        self.ui.statusLabel.setText("Something went wrong. \n You might not "
                                    "have a internet connection \n\n We have logged it "
                                    "so we can take a look.")
                                    
        self.ui.label.setPixmap(QPixmap(":/syncing/sad"))
        log("SYNC ERROR:" + text)
        self.ui.buttonBox.show()
        self.failed = True

    def runSync(self):
        self.ui.statusLabel.setText("Sycning with server. \n Please Wait")
        message = self.ui.statusLabel.text()
        self.syncer = Syncer()
        self.syncer.syncPass.connect(self.updateStatus)
        self.syncer.syncFailed.connect(self.updateFailedStatus)
        datamessage = message + "\n Syncing map data..."
        self.ui.statusLabel.setText(datamessage)
        self.syncer.doSync()

        if self.failed:
            return
        
        self.syncer = ImageSyncer()
        self.syncer.syncPass.connect(self.updateStatus)
        self.syncer.syncFailed.connect(self.updateFailedStatus)
        datamessage = message + "\n Syncing images..."
        self.ui.statusLabel.setText(datamessage)
        self.syncer.doSync()


if __name__ == "__main__":
    sync = ImageSyncer()
    sync.doSync()