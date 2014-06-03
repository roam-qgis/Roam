from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_textwidget_config import Ui_Form


class TextWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Free text field'

    def __init__(self, parent=None):
        super(TextWidgetConfig, self).__init__(parent)
        self.setupUi(self)


class TextBlockWidgetConfig(TextWidgetConfig):
    description = 'Large free text field'

    def __init__(self, parent=None):
        super(TextBlockWidgetConfig, self).__init__(parent)
