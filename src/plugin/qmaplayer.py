import os.path
from PyQt4.QtCore import QSettings,QString
from PyQt4.QtGui import QIcon
from PyQt4.uic import loadUi
import os
import imp
import json
import utils
import os

values_file = os.path.join(os.environ['APPDATA'], "QMap")

def getSavedValues(layer):
    attr = {}
    id = str(layer.id())
    savedvaluesfile = os.path.join(values_file, "%s.json" % id)
    try:
        utils.log(savedvaluesfile)
        with open(savedvaluesfile, 'r') as f:
            attr = json.loads(f.read())
    except IOError:
        utils.log('No saved values found for %s' % id)
    except ValueError:
        utils.log('No saved values found for %s' % id)
    return attr

def setSavedValues(layer, values):
    savedvaluesfile = os.path.join(values_file, "%s.json" % str(layer.id()))
    path = os.path.dirname(savedvaluesfile)
    if not os.path.exists(path):
        os.makedirs(path)

    with open(savedvaluesfile, 'w') as f:
        json.dump(values,f)


def getHelpFile(fieldname):
    # BROKEN.
    filename = "%s.html" % str(fieldname)
    filepath = os.path.join(name,"help", filename )
    if os.path.exists(filepath):
        return filepath
    else:
        return None



