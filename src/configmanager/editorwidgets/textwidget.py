import os

from admin_plugin.editorwidgets.core import WidgetFactory, ConfigWidget
from admin_plugin import create_ui

widget, base = create_ui(os.path.join("editorwidgets","uifiles",'textwidget_config.ui'))

class TextWidgetConfig(widget, ConfigWidget):
    def __init__(self, layer, field, parent=None):
        super(TextWidgetConfig, self).__init__(layer, field, parent)
        self.setupUi(self)

    def widgetchanged(self):
        self.widgetdirty.emit()

    def getconfig(self):
        config = {}
        return config

    def setconfig(self, config):
        self.blockSignals(True)
        self.blockSignals(False)

factory = WidgetFactory("Text", None, TextWidgetConfig)
factory.description = "Free text field"
factory.icon = ':/icons/text'
