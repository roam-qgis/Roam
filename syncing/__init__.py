import os
from subprocess import Popen, PIPE

def doSync():
    curdir= os.path.dirname(__file__)
    cmdpath =os.path.join(curdir,'bin\SyncProofConcept.exe')
    p = Popen(cmdpath, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell = True)
    stdout, stderr = p.communicate()
    
    if (stderr is None):
        return (True, stdout)
    else:
        return (False, stderr)

if __name__ == "__main__":
    print doSync()