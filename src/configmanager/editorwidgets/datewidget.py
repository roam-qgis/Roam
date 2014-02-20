from PyQt4.QtGui import QDateTimeEdit

from roam.editorwidgets.datewidget import DateWidget

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.datewidget_config import Ui_Form


class DateWidgetConfig(Ui_Form, ConfigWidget):
    description = "Date selector"

    def __init__(self, parent=None):
        super(DateWidgetConfig, self).__init__(parent)
        self.setupUi(self)
