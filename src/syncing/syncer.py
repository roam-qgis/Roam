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

from utils import log, settings

class Syncer(QObject):
    syncprogress = pyqtSignal(str)

    def syncMSSQL(self):
        """
        Run the sync for MS SQL.

        returns -- Returns a tuple of (state, message). state can be 'Pass' or
                   'Fail'
        """
        curdir = os.path.abspath(os.path.dirname(__file__))
        cmdpath = os.path.join(curdir,'bin\syncer.exe')
        server = "Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
        client = "Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"
        args = [cmdpath, '--server="{0}"'.format(server), '--client="{0}"'.format(server), '--porcelain']
        p = Popen(args, stdout=PIPE, stderr=PIPE, shell=True)
        while p.poll() is None:
            out = p.stdout.readline()
            # if out[0] == 't':
            #     pairs = out.split('|')
            #     for pair in pairs:
            #         pair.splt(":")
            self.syncprogress.emit(out)

    def syncImages(self):
        """
        Run the sync over the images

        returns -- Returns a tuple of (state, message). state can be 'Pass' or
                   'Fail'
        """
        images = os.path.join(pardir, "data")
        server = settings.value("syncing/server_image_location").toString()
        if server.isEmpty():
            return ('Fail', "No server image location found in settings.ini")

        if not os.path.exists(images):
            # Don't return a fail if there is no data directory
            return ('Pass', 'Images uploaded: %s' % str(0))

        cmd = 'xcopy "%s" "%s" /Q /D /S /E /K /C /H /R /Y' % (images, server)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell = True)
        stdout, stderr = p.communicate()
        if not stderr == "":
            return ('Fail', stderr)
        else:
            return ('Pass', stdout)
       

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
        self.ui.statusLabel.setText("We couldn't sync for some reason. \n "\
                                    "Dont' worry you might just not have an " \
                                    "internet connection at this time" \
                                    "\n\n We have logged it "
                                    "so we can take a look. Just in case.")
                                    
        self.ui.label.setPixmap(QPixmap(":/syncing/sad"))
        log("SYNC ERROR:" + text)
        self.ui.buttonBox.show()
        self.failed = True

    def runSync(self):
        """
        Shows the sync dialog and runs the sync commands.
        """
        self.ui.statusLabel.setText("Syncing with server. \n Please Wait")
        message = self.ui.statusLabel.text()
        self.ui.statusLabel.setText(message + "\n\n Syncing map data...")
        QCoreApplication.processEvents()

        sync = Syncer()
        sync.syncprogress.connect(self.pushupdate)
        
        sync.syncMSSQL()

        # if state == 'Fail':
        #     self.updateFailedStatus(sqlmsg)
        #     return

        # log(sqlmsg)

        # self.ui.statusLabel.setText(message + "\n\n Syncing images...")
        # QCoreApplication.processEvents()
        
        # state, msg = syncImages()

        # if state == 'Fail':
        #     self.updateFailedStatus(msg)
        #     return

        # self.updateStatus("%s \n %s" % (sqlmsg, msg))

    def pushupdate(self, message):
        QCoreApplication.processEvents()
        self.ui.statusLabel.setText(message)
        QCoreApplication.processEvents()