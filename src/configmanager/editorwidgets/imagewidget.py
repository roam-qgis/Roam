from roam.editorwidgets.imagewidget import ImageWidget

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.photowidget_config import Ui_Form


class ImageWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Allow the user to select an image'

    def __init__(self, parent=None):
        super(ImageWidgetConfig, self).__init__(parent)
        self.setupUi(self)
        self.defaultLocationText.textChanged.connect(self.widgetchanged)

    def getconfig(self):
        location = self.defaultLocationText.text()
        return {"defaultlocation": location}

    def setconfig(self, config):
        self.defaultLocationText.setText(config.get('defaultlocation', ''))

