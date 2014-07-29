import os

from functools import partial

from PyQt4.QtGui import QWidget
from PyQt4.QtCore import Qt
from qgis.core import QgsMapLayer

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_option_config import Ui_Form


class OptionWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Select a item from a row of buttons'

    def __init__(self, parent=None):
        super(OptionWidgetConfig, self).__init__(parent)
        self.setupUi(self)

    def getconfig(self):
        config = {}
        config['list'] = {}
        config['list']['items'] = [item for item in self.listText.toPlainText().split('\n')]
        return config

    def setconfig(self, config):
        self.blockSignals(True)
        subconfig = config.get('list', {})
        self.list = subconfig.get('items', [])
        itemtext = '\n'.join(self.list)
        self.listText.setPlainText(itemtext)
        self.blockSignals(False)

