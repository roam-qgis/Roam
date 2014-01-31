from PyQt4.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap
from PyQt4.QtCore import QByteArray, pyqtSignal

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

    def showlargeimage(self, pixmap):
        self.openimage.emit(pixmap)

    def setvalue(self, value):
        self.widget.loadImage(value)

    def value(self):
        return self.widget.getImage()

