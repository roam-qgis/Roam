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
        self.saveToDBCheck.clicked.connect(self.widgetchanged)
        self.externalDBLayer.textChanged.connect(self.widgetchanged)
        self.externalDBText.textChanged.connect(self.widgetchanged)
        self.maxPhotosSpin.valueChanged.connect(self.widgetchanged)

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
        if self.saveToDBCheck.isChecked():
            configdata['savetodb'] = True
            configdata['dboptions'] = {
                "dbpath": self.externalDBText.text(),
                "table": self.externalDBLayer.text(),
                "maximages": self.maxPhotosSpin.value()
            }
        return configdata


    def setconfig(self, config):
        self.defaultLocationText.setText(config.get('defaultlocation', ''))
        self.savetofileCheck.setChecked(config.get('savetofile', False))
        stamp = config.get('stamp', dict(value='', position='top-left'))
        self.imageStampText.setPlainText(stamp['value'])
        index = self.imageStampLocation.findText(stamp['position'])
        self.imageStampLocation.setCurrentIndex(index)
        savetodb = config.get('savetodb', False)
        self.saveToDBCheck.setChecked(savetodb)
        if savetodb:
            dboptions = config['dboptions']
            self.externalDBLayer.setText(dboptions.get('table', ''))
            self.externalDBText.setText(dboptions.get('dbpath', ''))
            self.maxPhotosSpin.setValue(dboptions.get('maximages', 1))

