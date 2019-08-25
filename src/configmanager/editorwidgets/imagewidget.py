from PyQt5.QtWidgets import QFileDialog

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_photowidget_config import Ui_Form
from configmanager.editorwidgets.uifiles import ui_multiphotowidget_config

class MultiImageWidgetConfig(ui_multiphotowidget_config.Ui_Form, ConfigWidget):
    description = 'Allow the user to select an multi images.'

    def __init__(self, parent=None):
        super(MultiImageWidgetConfig, self).__init__(parent)
        self.setupUi(self)
        self.defaultLocationText.textChanged.connect(self.widgetchanged)
        self.imageStampText.textChanged.connect(self.widgetchanged)
        self.locatioButton.pressed.connect(self.openfilepicker)
        self.externalDBLayer.textChanged.connect(self.widgetchanged)
        self.externalDBText.textChanged.connect(self.widgetchanged)
        self.maxPhotosSpin.valueChanged.connect(self.widgetchanged)
        self.linkcodeText.textChanged.connect(self.widgetchanged)

    def openfilepicker(self):
        startpath = self.defaultLocationText.text() or '/home'
        path = QFileDialog.getExistingDirectory(self.parent(), "Select default photo location", startpath)
        self.defaultLocationText.setText(path)

    def getconfig(self):
        location = self.defaultLocationText.text()
        imagestamp = self.imageStampText.toPlainText()
        stamplocation = self.imageStampLocation.currentText()
        configdata = {"defaultlocation": location,
                      'stamp': dict(value=imagestamp,
                                    position=stamplocation)}
        configdata['dboptions'] = {
            "dbpath": self.externalDBText.text(),
            "table": self.externalDBLayer.text(),
            "maximages": self.maxPhotosSpin.value(),
            "linkcode": self.linkcodeText.text()
        }
        return configdata


    def setconfig(self, config):
        self.defaultLocationText.setText(config.get('defaultlocation', ''))
        stamp = config.get('stamp', dict(value='', position='top-left'))
        self.imageStampText.setPlainText(stamp['value'])
        index = self.imageStampLocation.findText(stamp['position'])
        self.imageStampLocation.setCurrentIndex(index)
        dboptions = config.get('dboptions', {})
        self.externalDBLayer.setText(dboptions.get('table', ''))
        self.externalDBText.setText(dboptions.get('dbpath', ''))
        self.maxPhotosSpin.setValue(dboptions.get('maximages', 1))
        self.linkcodeText.setText(dboptions.get('linkcode','photo'))


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
        configdata = {"defaultlocation": location,
                'savetofile': savetofile,
                'stamp': dict(value=imagestamp,
                              position=stamplocation)}
        return configdata


    def setconfig(self, config):
        self.defaultLocationText.setText(config.get('defaultlocation', ''))
        self.savetofileCheck.setChecked(config.get('savetofile', False))
        stamp = config.get('stamp', dict(value='', position='top-left'))
        self.imageStampText.setPlainText(stamp['value'])
        index = self.imageStampLocation.findText(stamp['position'])
        self.imageStampLocation.setCurrentIndex(index)
