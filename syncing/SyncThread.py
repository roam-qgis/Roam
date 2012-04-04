from PyQt4.QtCore import QThread,pyqtSignal
import os
from subprocess import Popen, PIPE

def doSync():
    curdir= os.path.dirname(__file__)
    cmdpath =os.path.join(curdir,'bin\SyncProofConcept.exe')
    p = Popen(cmdpath, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell = True)
    stdout, stderr = p.communicate()
    
    if (stderr == ""):
        return (True, stdout)
    else:
        return (False, stderr)

class SyncThread( QThread ):
    syncFinished = pyqtSignal(bool, str)
    def __init__(self, parent=None):
        QThread.__init__(self,parent)

    def run(self):
        succes, message = doSync()
        self.syncFinished.emit( succes, message )