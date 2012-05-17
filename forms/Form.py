import os.path
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QIcon
from PyQt4.uic import loadUi
import os

class Form(object):
    """
    Represents a data collection form.  Contains links to the python module for the form.
    """

    def __init__(self, module):
        self._module = module
        
    @property
    def module(self):
        return self._module

    def formInstance(self):
        path = os.path.dirname(self.module.__file__())
        uiFile = os.path.join(path, "form.ui")
        return loadUi(uiFile)

    def settings(self):
        if self._settings is None:
            path = os.path.dirname(self.module.__file__())
            self._settings = QSettings(os.path.join(path, "settings.ini"), QSettings.IniFormat )

        return self._settings

    def layerName(self):
        return self.settings.value("layer_name").toString()

    def formName(self):
        return self.settings.value("form_name").toString()

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(self.module.__file__),'icon.png'))