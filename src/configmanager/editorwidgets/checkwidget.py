import os

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QComboBox

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_checkwidget_config import Ui_Form


class CheckboxWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Checkbox with changeable true false values'

    def __init__(self, parent=None):
        super(CheckboxWidgetConfig, self).__init__(parent)
        self.setupUi(self)
        self.checkedText.textChanged.connect(self.widgetchanged)
        self.uncheckedText.textChanged.connect(self.widgetchanged)

    def getconfig(self):
        config = {}
        config['checkedvalue'] = self.checkedText.text()
        config['uncheckedvalue'] = self.uncheckedText.text()
        return config

    def setconfig(self, config):
        self.blockSignals(True)
        self.checkedText.setText(str(config.get('checkedvalue', 0)))
        self.uncheckedText.setText(str(config.get('uncheckedvalue', 0)))
        self.blockSignals(False)
