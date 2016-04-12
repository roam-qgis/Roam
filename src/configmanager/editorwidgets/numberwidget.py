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
        self.places_spin.setVisible(False)
        self.places_label.setVisible(False)

    def getconfig(self):
        config = {}
        config['max'] = self.maxEdit.text()
        config['min'] = self.minEdit.text()
        config['prefix'] = self.prefixEdit.text()
        config['suffix'] = self.suffixEdit.text()
        config['step'] = int(self.step_spin.value())
        return config

    def setconfig(self, config):
        self.blockSignals(True)
        max = config.get('max', '')
        min = config.get('min', '')
        prefix = config.get('prefix', '')
        suffix = config.get('suffix', '')
        step = config.get('step', 1)
        self.minEdit.setText(min)
        self.maxEdit.setText(max)
        self.prefixEdit.setText(prefix)
        self.step_spin.setValue(int(step))
        self.suffixEdit.setText(suffix)
        self.blockSignals(False)


class DoubleNumberWidgetConfig(NumberWidgetConfig):
    description = 'Double number entry widget'

    def __init__(self, parent=None):
        super(DoubleNumberWidgetConfig, self).__init__(parent)
        self.places_spin.setVisible(True)
        self.places_label.setVisible(True)
        self.places_spin.valueChanged.connect(self.widgetchanged)

    def getconfig(self):
        config = super(DoubleNumberWidgetConfig, self).getconfig()
        config['places'] = self.places_spin.value()
        config['step'] = self.step_spin.value()
        return config

    def setconfig(self, config):
        super(DoubleNumberWidgetConfig, self).setconfig(config)
        self.blockSignals(True)
        places = config.get('places', 2)
        self.places_spin.setValue(places)
        self.blockSignals(False)

