from PyQt4.QtCore import QObject, pyqtSignal
from os import path
import sys
from subprocess import Popen, PIPE
from qmap.utils import log, settings

class Syncer(QObject):
    syncingtable = pyqtSignal(str, int)
    syncingfinished = pyqtSignal(int, int)
    syncingerror = pyqtSignal(str)

    def __init__(self, func=None):
        super(Syncer, self).__init__()
        self.func = func

    def sync(self):
        self.func(self)

def syncMSSQL(self):
    """
    Run the sync for MS SQL.

    """
    curdir = path.abspath(path.dirname(__file__))
    cmdpath = path.join(curdir,'syncer.exe')
    server = settings.value("syncing/server").toPyObject()
    client = settings.value("syncing/client").toPyObject()
    args = [cmdpath, '--server={0}'.format(server), '--client={0}'.format(client), '--porcelain']
    # We have to PIPE stdin even if we don't use it because of Windows  
    p = Popen(args, stdout=PIPE, stderr=PIPE,stdin=PIPE, shell=True)
    while p.poll() is None:
        # error = p.stderr.readline()
        # print "ERROR:" + error 
        out = p.stdout.readline()
        try:
            # Can't seem to get p.stderr to work correctly. Will use this hack for now.
            if out[:5] == "Error":
                log(out)
                self.syncingerror.emit(out)
                continue
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
            # We should really log errors but don't show them to the user
            pass

def syncImages(self):
    """
    Run the sync over the images

    returns -- Returns a tuple of (state, message). state can be 'Pass' or
               'Fail'
    """
    images = path.join(pardir, "data")
    server = settings.value("syncing/server_image_location").toString()
    if server.isEmpty():
        return ('Fail', "No server image location found in settings.ini")

    if not path.exists(images):
        # Don't return a fail if there is no data directory
        return ('Pass', 'Images uploaded: %s' % str(0))

    cmd = 'xcopy "%s" "%s" /Q /D /S /E /K /C /H /R /Y' % (images, server)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell = True)
    stdout, stderr = p.communicate()
    if not stderr == "":
        return ('Fail', stderr)
    else:
        return ('Pass', stdout)

syncproviders = [Syncer(syncMSSQL)]

