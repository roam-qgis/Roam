import os

from PyQt4.QtGui import QDateTimeEdit

from admin_plugin.editorwidgets.core import WidgetFactory, ConfigWidget
from admin_plugin import create_ui

widget, base = create_ui(os.path.join("editorwidgets","uifiles", 'datewidget_config.ui'))

class DateWidgetConfig(widget, ConfigWidget):
    def __init__(self, layer, field, parent=None):
        super(DateWidgetConfig, self).__init__(layer, field, parent)
        self.setupUi(self)

    def getconfig(self):
        config = {}
        return config

    def setconfig(self, config):
        self.blockSignals(True)
        self.blockSignals(False)

factory = WidgetFactory("Date", None,  DateWidgetConfig)
factory.description = "Date selector"
factory.icon = ':/icons/date2'
