from PyQt4.QtGui import QDialog, QApplication
from PyQt4.QtCore import Qt, QCoreApplication
from ui_sync import Ui_syncForm
from qmap.utils import log, error, _pluralstring

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

    def runSync(self, providers):
        """
        Shows the sync dialog and runs the sync commands.
        """
        for provider in providers:
            provider.syncstatus.connect(self.syncstatus)
            provider.syncingfinished.connect(self.syncfinsihed)
            provider.sync()

    def syncfinsihed(self, down, up, errors):
        errormessage = _pluralstring("Error", len(errors))
        message = "Total Downloaded: {0}\nTotal Uploaded: {1}\n{2}".format(down,up, errormessage)

        self.ui.statusLabel.setText(message)
        self.ui.header.setText("Sync complete")
        self.ui.buttonBox.setEnabled(True)
        QCoreApplication.processEvents()

    def syncstatus(self, layer, changes):
        # ewww
        if changes == 0:
            return

        changemessage = _pluralstring("change", changes)
        message = "Updated layer {0} with {1}".format(layer, changemessage)
        self.ui.updatestatus.addItem(message)
        QCoreApplication.processEvents()