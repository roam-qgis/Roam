from PyQt4.QtCore import pyqtSignal, QProcess, QObject
from qmap.utils import log


class SyncProvider(QObject):
    syncComplete = pyqtSignal(str)
    syncStarted = pyqtSignal()
    syncMessage = pyqtSignal(str)
    syncError = pyqtSignal(str)
    
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
        
    def startSync(self):
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
        self.output += str(self.process.readAll())    
        html = """<h3> {0} sync report </h3>
                  <pre>{1}</pre>""".format(self.name, self.output)
                         
        if error > 0 or self.haserror:
            html = """<h3> {0} Error </h3>
                  <pre>{1}</pre>""".format(self.name, self.output)
            self.syncError.emit("Error with sync")
        else:
            self.syncComplete.emit(html)
    
    def readOutput(self):
        self.output += str(self.process.readAll())
        
        html = """<h3> {0} progress report </h3>
                  <pre>{1}</pre>""".format(self.name, self.output)
                  
        self.syncMessage.emit(html)