from PyQt4.QtCore import pyqtSignal, QProcess, QObject
from qmap.utils import log


class SyncProvider(QObject):
    syncComplete = pyqtSignal()
    syncStarted = pyqtSignal()
    syncMessage = pyqtSignal(str)
    syncError = pyqtSignal()
    
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
        self.process.finished.connect(self.syncComplete)
        self.process.started.connect(self.syncStarted)
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.output = None
        
    def startSync(self):
        self.data = None
        self.process.start(self.cmd, [])
        
    def getReport(self):
        if not self.output:
            self.output = self.process.readAllStandardOutput()
        
        html = """<h3> {0} sync report </h3>
                  <pre>{1}</pre>""".format(self.name, self.output)
        log(self.output)
        return html
    
    def readOutput(self):
        output = self.process.readLine()
        
        html = """<h3> {0} status report </h3>
                  <pre>{1}</pre>""".format(self.name, output)
                  
        self.syncMessage.emit(html)