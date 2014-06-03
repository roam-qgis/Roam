import os

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QComboBox, QDoubleValidator

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_numberwidget_config import Ui_Form

class NumberWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Number entry widget'

    def __init__(self, parent=None):
        super(NumberWidgetConfig, self).__init__(parent)
        self.setupUi(self)
        self.minEdit.setValidator( QDoubleValidator() )
        self.maxEdit.setValidator( QDoubleValidator() )

        self.minEdit.textChanged.connect(self.widgetchanged)
        self.maxEdit.textChanged.connect(self.widgetchanged)
        self.prefixEdit.textChanged.connect(self.widgetchanged)
        self.suffixEdit.textChanged.connect(self.widgetchanged)

    def getconfig(self):
        config = {}
        config['max'] = self.maxEdit.text()
        config['min'] = self.minEdit.text()
        config['prefix'] = self.prefixEdit.text()
        config['suffix'] = self.suffixEdit.text()
        return config

    def setconfig(self, config):
        self.blockSignals(True)
        max = config.get('max', '')
        min = config.get('min', '')
        prefix = config.get('prefix', '')
        suffix = config.get('suffix', '')
        self.minEdit.setText(min)
        self.maxEdit.setText(max)
        self.prefixEdit.setText(prefix)
        self.suffixEdit.setText(suffix)
        self.blockSignals(False)

