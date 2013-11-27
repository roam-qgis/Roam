from PyQt4.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap
from PyQt4.QtCore import QByteArray

from roam.editorwidgets.core import WidgetFactory, EditorWidget
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget


class ImageWidget(EditorWidget):
    def __init__(self, *args):
        super(ImageWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QMapImageWidget(parent)

    def initWidget(self, widget):
        widget.openRequest.connect(self.showlargeimage)
        widget.imageloaded.connect(self.validate)
        widget.imageremoved.connect(self.validate)

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
        if isinstance(value, QByteArray):
            self.widget.loadImage(value)
        else:
            self.widget.loadFromPixMap(QPixmap(value))

    def value(self):
        pass

factory = WidgetFactory("Image", ImageWidget, None)

