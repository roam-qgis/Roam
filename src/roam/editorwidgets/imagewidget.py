from PyQt4.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap
from PyQt4.QtCore import QByteArray

from roam.editorwidgets.core import EditorWidget
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget


class ImageWidget(EditorWidget):
    widgettype = 'Image'

    def __init__(self, *args):
        super(ImageWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QMapImageWidget(parent)

    def initWidget(self, widget):
        widget.openRequest.connect(self.showlargeimage)
        widget.imageloaded.connect(self.validate)
        widget.imageremoved.connect(self.validate)
        widget.defaultlocation = self.config.get('defaultlocation', '')

    def validate(self, *args):
        self.raisevalidationupdate(not self.widget.isDefault)

    def showlargeimage(self, pixmap):
        dlg = QDialog()
        dlg.setWindowTitle("Image Viewer")
        dlg.setLayout(QGridLayout())
        dlg.layout().setContentsMargins(0, 0, 0, 0)
        dlg.layout().setSizeConstraint(QLayout.SetNoConstraint)
        dlg.resize(600, 600)
        label = QLabel()
        label.mouseReleaseEvent = lambda x: dlg.accept()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        dlg.layout().addWidget(label)
        dlg.exec_()
        pass

    def setvalue(self, value):
        self.widget.loadImage(value)

    def value(self):
        return self.widget.getImage()

