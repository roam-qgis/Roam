import os.path
from PyQt4.QtCore import QSettings,QString
from PyQt4.QtGui import QIcon
from PyQt4.uic import loadUi
import os
import imp
import json
import utils

def getForms():
    """ Get all the custom user forms that have been created.
    Checks for "form" at the start to detect module as custom form

    @Returns A list of modules that contain user forms.
    """
    forms = {}
    curdir = os.path.abspath(os.path.dirname(__file__))
    formspath = os.path.join(curdir,'entry_forms')
    for module in os.listdir(formspath):
        if module[:4] == 'form':
            if os.path.exists(os.path.join(formspath,module,"settings.config")):
                instance = loadFormModule(module)
                form = Form(instance)
                for layername in form.layers():
                    forms[layername] = form

    return forms

def loadFormModule(module):
    """ Load the forms module """
    formmodule = __import__("qmap.entry_forms.%s" % module, locals(), globals(),["*"], 1)
    return formmodule

class Form(object):
    """
    Represents a data collection form.  Contains links to the python module for the form.
    """
    def __init__(self, module):
        self._module = module
        self._settings = None
        self._db = None
        self.name = os.path.dirname(self.module.__file__)
        self.savedvaluesfile = os.path.join(self.name , "savedvalues.json")

    @property
    def module(self):
        return self._module

    def formInstance(self, parent=None):
        uiFile = os.path.join(self.name, "form.ui")
        instance = loadUi(uiFile)
        return instance

    def settings(self):
        if self._settings is None:
            with open(os.path.join(self.name, "settings.config"),'r') as f:
                self._settings = json.load(f)

        return self._settings
    
    def getHelpFile(self, fieldname):
        filename = "%s.html" % str(fieldname)
        filepath = os.path.join(self.name,"help", filename )
        if os.path.exists(filepath):
            return filepath
        else:
            return None

    def getSavedValues(self):
        attr = {}
        try:
            utils.log(self.savedvaluesfile)
            with open(self.savedvaluesfile, 'r') as f:
                attr = json.loads(f.read())
        except IOError:
            utils.log('No saved values found for %s' % self.name)
        except ValueError:
            utils.log('No saved values found for %s' % self.name)
        return attr

    def setSavedValues(self, values):
        path = os.path.dirname(self.savedvaluesfile)
        if not os.path.exists(path):
            makedirs(path)

        with open(self.savedvaluesfile, 'w') as f:
            json.dump(values,f)

    def layers(self):
        """
        Returns a list of layer names this form can be used with
        """
        return self.settings()["layers"].keys()

    def nameforform(self, layer):
        """
        Return the text for the form
        """
        return self.settings()["layers"][layer]["text"]

    def icon(self):
        """
        Return the icon for the form
        """
        # TODO Return a icon for each 
        return QIcon(os.path.join(os.path.dirname(self.module.__file__),'icon.png'))