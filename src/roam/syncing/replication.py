from PyQt4.QtCore import pyqtSignal, QProcess, QObject


class SyncProvider(QObject):
    syncComplete = pyqtSignal()
    syncStarted = pyqtSignal()
    syncMessage = pyqtSignal(str)
    syncError = pyqtSignal(str)
    syncFinished = pyqtSignal()
    
    def startSync(self):
        pass
    
    def getReport(self):
        return "<p>No report for sync provider generated<p>"
    

class ReplicationSync(SyncProvider):
    def __init__(self, name, cmd):
        super(SyncProvider, self).__init__()
        self.name = name
        self.cmd = cmd
        self.process = QProcess()
        self.process.finished.connect(self.complete)
        self.process.started.connect(self.syncStarted)
        self.process.readyReadStandardError.connect(self.error)
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self._output = ""
        self.haserror = False
        
    def start(self):
        self._output = ""
        self.process.start(self.cmd, [])
        
    @property
    def output(self):
        return self._output
    
    @output.setter   
    def output(self, value):
        self._output = value
        
    def error(self):
        self.haserror = True
        
    def complete(self, error, status):
        print "Complete"
        if error > 0:
            print "Error"
            self.syncError.emit('On snap!')
        else:
            self.syncComplete.emit()
        self.syncFinished.emit()
    
    def readOutput(self):
        output = str(self.process.readAll())
        self.syncMessage.emit(output)