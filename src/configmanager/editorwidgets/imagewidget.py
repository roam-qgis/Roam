from PyQt4.QtGui import QFileDialog

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_photowidget_config import Ui_Form


class ImageWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Allow the user to select an image'

    def __init__(self, parent=None):
        super(ImageWidgetConfig, self).__init__(parent)
        self.setupUi(self)
        self.defaultLocationText.textChanged.connect(self.widgetchanged)
        self.imageStampText.textChanged.connect(self.widgetchanged)
        self.savetofileCheck.stateChanged.connect(self.widgetchanged)
        self.locatioButton.pressed.connect(self.openfilepicker)

    def openfilepicker(self):
        startpath = self.defaultLocationText.text() or '/home'
        path = QFileDialog.getExistingDirectory(self.parent(), "Select default photo location", startpath)
        self.defaultLocationText.setText(path)

    def getconfig(self):
        location = self.defaultLocationText.text()
        savetofile = self.savetofileCheck.isChecked()
        imagestamp = self.imageStampText.toPlainText()
        stamplocation = self.imageStampLocation.currentText()
        return {"defaultlocation": location,
                'savetofile': savetofile,
                'stamp': dict(value=imagestamp,
                              position=stamplocation)}

    def setconfig(self, config):
        self.defaultLocationText.setText(config.get('defaultlocation', ''))
        self.savetofileCheck.setChecked(config.get('savetofile', False))
        stamp = config.get('stamp', dict(value='', position='top-left'))
        self.imageStampText.setPlainText(stamp['value'])
        index = self.imageStampLocation.findText(stamp['position'])
        self.imageStampLocation.setCurrentIndex(index)
