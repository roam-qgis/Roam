import os

from admin_plugin.editorwidgets.core import WidgetFactory, ConfigWidget
from admin_plugin import create_ui

image_widget, image_base = create_ui(os.path.join("editorwidgets","uifiles",'photowidget_config.ui'))

class ImageWidgetConfig(image_widget, ConfigWidget):
    def __init__(self, layer, field, factory, parent=None):
        super(ImageWidgetConfig, self).__init__(layer, field, parent)
        self.setupUi(self)
        self.defaultLocationText.textChanged.connect(self.widgetdirty.emit)

    def getconfig(self):
        location = self.defaultLocationText.text()
        return {"defaultlocation" : location }

    def setconfig(self, config):
        self.defaultLocationText.setText(config.get('defaultlocation', ''))

factory = WidgetFactory("Image", None, ImageWidgetConfig)
factory.description = 'Allow the user to select an image'
factory.icon = ":/icons/picture"
