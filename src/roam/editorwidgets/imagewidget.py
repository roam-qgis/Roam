from PyQt4.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap
from PyQt4.QtCore import QByteArray, pyqtSignal, QVariant

from roam.editorwidgets.core import EditorWidget
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget


class ImageWidget(EditorWidget):
    widgettype = 'Image'
    openimage = pyqtSignal(object)

    def __init__(self, *args):
        super(ImageWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QMapImageWidget(parent)

    def initWidget(self, widget):
        widget.openRequest.connect(self.showlargeimage)
        widget.imageloaded.connect(self.validate)
        widget.imageremoved.connect(self.validate)

    def updatefromconfig(self):
        self.widget.defaultlocation = self.config.get('defaultlocation', '')

    def validate(self, *args):
        self.raisevalidationupdate(not self.widget.isDefault)
        self.emitvaluechanged()

    def showlargeimage(self, pixmap):
        self.openimage.emit(pixmap)

    def setvalue(self, value):
        field = self.layer.pendingFields().field(self.field)
        if field.type() == QVariant.String and value:
            value = QByteArray.fromBase64(value)
        self.widget.loadImage(value)

    def value(self):
        field = self.layer.pendingFields().field(self.field)
        image = self.widget.getImage()
        if field.type() == QVariant.String and image:
            image = image.toBase64()
            return image.data()

        return image

