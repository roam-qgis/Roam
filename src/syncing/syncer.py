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
    syncingtable = pyqtSignal(str, int)
    syncingfinished = pyqtSignal(int, int)

    def syncMSSQL(self):
        """
        Run the sync for MS SQL.

        returns -- Returns a tuple of (state, message). state can be 'Pass' or
                   'Fail'
        """
        curdir = os.path.abspath(os.path.dirname(__file__))
        cmdpath = os.path.join(curdir,'syncer.exe')
        # TODO Get connection strings from the settings.ini file.
        server = "Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
        client = "Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"
        print server
        print client
        args = [cmdpath, '--server={0}'.format(server), '--client={0}'.format(client), '--porcelain']
        # We have to PIPE stdin even if we don't use it because of Windows  
        p = Popen(args, stdout=PIPE, stderr=PIPE,stdin=PIPE, shell=True)
        while p.poll() is None:
            # error = p.stderr.readline()
            # print "ERROR:" + error 
            out = p.stdout.readline()
            try:
                values = dict(item.split(":") for item in out.split("|"))
                if 'td' in values and 'tu' in values:
                    downloads = int(values.get('td'))
                    uploads = int(values.get('tu'))
                    self.syncingfinished.emit(downloads, uploads)

                elif 't' in values:
                    table = values.get('t')
                    inserts = int(values.get('i'))
                    deletes = int(values.get('d'))
                    updates = int(values.get('u'))
                    changes = inserts + deletes + updates
                    self.syncingtable.emit(table, changes)
                else:
                    message = out 
                
            except ValueError:
                # Log but don't show it to the user
                pass

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
        message = "Total Downloaded:\nTotal Uploaded:"
        self.ui.updatestatus.setText('')
        self.ui.statusLabel.setText(message)

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
        sync = Syncer()
        sync.syncingtable.connect(self.tableupdate)
        sync.syncingfinished.connect(self.syncfinsihed)
        sync.syncMSSQL()

        self.ui.buttonBox.show()

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

    def syncfinsihed(self, down, up):
        QCoreApplication.processEvents()
        message = "Total Downloaded: {0}\nTotal Uploaded: {1}".format(down,up)
        self.ui.updatestatus.setText('')
        self.ui.statusLabel.setText(message)
        self.ui.header.setText("Sync complete")
        QCoreApplication.processEvents()
        
    def tableupdate(self, table, changes):
        # ewww
        QCoreApplication.processEvents()
        message = "Updated layer {0} with {1} changes".format(table, changes)
        self.ui.updatestatus.setText(message)
        QCoreApplication.processEvents()

def update(message):
    print message

if __name__ == "__main__":
    app = QApplication([])
    syndlg = SyncDialog()
    syndlg.setModal(True)
    syndlg.show()
    # HACK
    QCoreApplication.processEvents()
    syndlg.runSync()

    app.exec_()