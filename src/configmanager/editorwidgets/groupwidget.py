from roam.editorwidgets.textwidget import GroupWidget

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.groupwidget_config import Ui_Form


class GroupWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Group'

    def __init__(self, parent=None):
        super(GroupWidgetConfig, self).__init__(parent)
        self.setupUi(self)


