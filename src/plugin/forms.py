import os.path
from PyQt4.QtCore import QSettings,QString
from PyQt4.QtGui import QIcon
from PyQt4.uic import loadUi
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
import os
import imp
import json

def getForms():
    """ Get all the custom user forms that have been created.
    Checks for "form" at the start to detect module as custom form

    @Returns A list of modules that contain user forms.
    """
    modules = []
    curdir = os.path.abspath(os.path.dirname(__file__))
    formspath = os.path.join(curdir,'entry_forms')
    for module in os.listdir(formspath):
        if module[:4] == 'form':
            if os.path.exists(os.path.join(formspath,module,"settings.config")):
                instance = loadFormModule(module)
                modules.append(Form(instance))

    return modules

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

    @property
    def module(self):
        return self._module

    def formInstance(self, parent=None):
        path = os.path.dirname(self.module.__file__)
        uiFile = os.path.join(path, "form.ui")
        instance = loadUi(uiFile)
        return instance

    def db(self):
        """
            Get or create the form.db database instance and the needed tables.
        """
        if self._db is None:
            path = os.path.dirname(self.module.__file__)
            dbpath = os.path.join(path, "form.db")
            self._db = QSqlDatabase.addDatabase("QSQLITE")
            self._db.setDatabaseName(dbpath)
            self._db.open()
            self.checkDatabaseTables()
        return self._db

    def checkDatabaseTables(self):
        if not self.db().tables().contains('ComboBoxItems'):
            q = QSqlQuery("CREATE TABLE IF NOT EXISTS ComboBoxItems ( control TEXT, value TEXT)")
            q.exec_()
        if not self.db().tables().contains('DefaultValues'):
            q = QSqlQuery("CREATE TABLE IF NOT EXISTS DefaultValues ( control TEXT, value TEXT)")
            q.exec_()

    def settings(self):
        if self._settings is None:
            path = os.path.dirname(self.module.__file__)
            with open(os.path.join(path, "settings.config"),'r') as f:
                self._settings = json.load(f)

        return self._settings
    
    def getHelpFile(self, name):
        path = os.path.dirname(self.module.__file__)
        filename = "%s.html" % str(name)
        filepath = os.path.join(path,"help", filename )
        if os.path.exists(filepath):
            return filepath
        else:
            return None

    def layerName(self):
        return str(self.settings()["layer_name"])

    def formName(self):
        return str(self.settings()["form_name"])

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(self.module.__file__),'icon.png'))