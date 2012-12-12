from PyQt4.QtGui import QDialog, QApplication
from PyQt4.QtCore import Qt, QCoreApplication
from ui_sync import Ui_syncForm
from qmap.syncing.syncer import Syncer

class SyncDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_syncForm()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = QApplication.desktop().screenGeometry(0)
        self.move( scr.center() - self.rect().center() )
        self.failed = False
        self.ui.buttonBox.setEnabled(False)

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
        message = "Total Downloaded: {0}\nTotal Uploaded: {1}".format(down,up)
        self.ui.statusLabel.setText(message)
        self.ui.header.setText("Sync complete")
        self.ui.buttonBox.setEnabled(True)
        QCoreApplication.processEvents()

    def tableupdate(self, table, changes):
        # ewww
        if changes == 0:
            return
        message = self.ui.updatestatus.toPlainText()
        message += "\nUpdated layer {0} with {1} changes".format(table, changes)
        self.ui.updatestatus.setPlainText(message)
        QCoreApplication.processEvents()