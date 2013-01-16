from PyQt4.QtCore import QObject, pyqtSignal
from os import path
import sys
from subprocess import Popen, PIPE
from qmap.utils import log, settings, error

class Syncer(QObject):
    syncstatus = pyqtSignal(str, int)
    syncingfinished = pyqtSignal(int, int, list)
    syncingerror = pyqtSignal(str)

    def __init__(self, func=None):
        super(Syncer, self).__init__()
        self.func = func
        self.errors = []

    def sync(self):
        self.errors =  []
        self.func(self)

def syncMSSQL(self):
    """
    Run the sync for MS SQL.

    """
    curdir = path.abspath(path.dirname(__file__))
    cmdpath = path.join(curdir,'syncer.exe')
    server = settings["syncing"]["server"]
    client = settings["syncing"]["client"]
    args = [cmdpath, '--server={0}'.format(server), '--client={0}'.format(client), '--porcelain']
    # We have to PIPE stdin even if we don't use it because of Windows  
    p = Popen(args, stdout=PIPE, stderr=PIPE,stdin=PIPE, shell=True)
    while p.poll() is None:
        # error = p.stderr.readline()
        # print "ERROR:" + error 
        out = p.stdout.readline()
        log(out)
        try:
            # Can't seem to get p.stderr to work correctly. Will use this hack for now.
            if out[:5] == "Error":
                error(out)
                self.errors.append(out)
                self.syncingerror.emit(out)
                continue
            values = dict(item.split(":") for item in out.split("|"))
            if 'td' in values and 'tu' in values:
                downloads = int(values.get('td'))
                uploads = int(values.get('tu'))
                self.syncingfinished.emit(downloads, uploads, self.errors)
            elif 't' in values:
                table = values.get('t')
                inserts = int(values.get('i'))
                deletes = int(values.get('d'))
                updates = int(values.get('u'))
                changes = inserts + deletes + updates
                self.syncstatus.emit(table, changes)
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
    try:
        server = settings["syncing"]["server_image_location"]
    except KeyError:
        return ('Fail', "No server image location found in settings.config")

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

