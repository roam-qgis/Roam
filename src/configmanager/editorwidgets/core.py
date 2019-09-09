from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget


class ConfigWidget(QWidget):
    """
    A base config widget class.
    """
    # Description of the widget to be shown in the UI.
    description = ""
    # Emit when anything in the config widget changes.
    widgetdirty = pyqtSignal(object)

    def __init__(self, parent=None):
        super(ConfigWidget, self).__init__(parent)
        self.defaultvalue = None

    def widgetchanged(self, *args, **kwargs):
        self.widgetdirty.emit(self.getconfig())

    def getconfig(self):
        return {}

    def setconfig(self, config):
        pass
