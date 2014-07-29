"""
Watches the src folder for changes to .ui, .qrc files and rebuilds the resources.
"""

import os
import hashlib
import time


def checkfiles():
    hash1 = None
    def getfiles():
        for root, _, files in os.walk("src"):
            for file in files:
                if file.endswith(".ui") or file.endswith('.qrc'):
                    yield os.path.join(root, file)

    while True:
        hasher = hashlib.md5()
        for file in getfiles():
            with open(file, 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)

        hash2 = hasher.hexdigest()
        if not hash2 == hash1:
            hash1 = hash2
            print "Files changed. Rebuilding..."
            os.system('python setup.py build')

        time.sleep(2)

checkfiles()
