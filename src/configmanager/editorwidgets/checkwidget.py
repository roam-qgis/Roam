import os

from PyQt4.QtGui import QComboBox

from admin_plugin.editorwidgets.core import WidgetFactory, ConfigWidget
from admin_plugin import create_ui

widget, base = create_ui(os.path.join("editorwidgets", 'uifiles', 'checkwidget_config.ui'))

class CheckWidgetConfig(widget, ConfigWidget):
    def __init__(self, layer, field, parent=None):
        super(CheckWidgetConfig, self).__init__(layer, field, parent)
        self.setupUi(self)

    def getconfig(self):
        config = {}
        config['checkedvalue'] = self.checkedText.text()
        config['uncheckedvalue'] = self.uncheckedText.text()
        return config

    def setconfig(self, config):
        self.blockSignals(True)
        self.checkedText.setText(config['checkedvalue'])
        self.uncheckedText.setText(config['uncheckedvalue'])
        self.blockSignals(False)

factory = WidgetFactory("Checkbox", None, CheckWidgetConfig)
factory.description = "Checkbox with changeable true false values"
factory.icon = ':/icons/check'
