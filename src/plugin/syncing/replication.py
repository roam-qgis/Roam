from PyQt4.QtCore import pyqtSignal, QProcess, QObject
from qmap.utils import log


class SyncProvider(QObject):
    syncComplete = pyqtSignal()
    syncStarted = pyqtSignal()
    syncMessage = pyqtSignal()
    syncError = pyqtSignal()
    
    def startSync(self):
        pass
    
    def syncComplete(self):
        pass
    

class ReplicationSync(SyncProvider):
    def __init__(self, name, cmd):
        super(SyncProvider, self).__init__()
        self.name = name
        self.cmd = cmd
        self.process = QProcess()
        self.process.finished.connect(self.syncComplete)
        self.process.started.connect(self.syncStarted)
        
    def startSync(self):
        self.process.start(self.cmd, [])
        log("START SYNC")
