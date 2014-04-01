import os

from PyQt4.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap, QFileDialog
from PyQt4.QtCore import QByteArray, pyqtSignal, QVariant

from roam.editorwidgets.core import EditorWidget
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget
from roam import utils



class ImageWidget(EditorWidget):
    widgettype = 'Image'
    openimage = pyqtSignal(object)

    def __init__(self, *args):
        super(ImageWidget, self).__init__(*args)
        self.tobase64 = False
        self.defaultlocation = ''

        if self.field and self.field.type() == QVariant.String:
            self.tobase64 = True

    def createWidget(self, parent):
        return QMapImageWidget(parent)

    def initWidget(self, widget):
        widget.openRequest.connect(self.showlargeimage)
        widget.imageloaded.connect(self.validate)
        widget.imageremoved.connect(self.validate)
        widget.imageloadrequest.connect(self._selectImage)

    def _selectImage(self):
        # Show the file picker
        defaultlocation = os.path.expandvars(self.defaultlocation)
        image = QFileDialog.getOpenFileName(self.widget, "Select Image", defaultlocation)
        utils.debug(image)
        if image is None or not image:
            return

        self.widget.loadImage(image)

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')

    def validate(self, *args):
        self.raisevalidationupdate(not self.widget.isDefault)
        self.emitvaluechanged()

    def showlargeimage(self, pixmap):
        self.openimage.emit(pixmap)

    def setvalue(self, value):
        if self.tobase64 and value:
            value = QByteArray.fromBase64(value)

        self.widget.loadImage(value)

    def value(self):
        image = self.widget.getImage()
        if self.tobase64 and image:
            image = image.toBase64()
            return image.data()

        return image

