import os

from PyQt4.QtGui import (QLabel, QDialog, QFileDialog,
                        QPixmap, QGridLayout, QLayout,
                        QWidget)
from PyQt4.QtCore import (QByteArray, QBuffer,
                        QIODevice, QEvent, QObject, pyqtSignal, Qt)


from roam.editorwidgets.uifiles import ui_imagewidget
import roam.utils
import roam.resources_rc


class QMapImageWidget(ui_imagewidget.Ui_imagewidget, QWidget):
    openRequest = pyqtSignal(QPixmap)
    imageloaded = pyqtSignal()
    imageremoved = pyqtSignal()
    imageloadrequest = pyqtSignal()
    annotateimage = pyqtSignal(QPixmap)


    def __init__(self, parent=None):
        super(QMapImageWidget, self).__init__(parent)
        self.setupUi(self)

        self._orignalimage = None
        self.setStyleSheet(":hover {background-color: #dddddd;}")
        self.selectbutton.clicked.connect(self.imageloadrequest.emit)
        self.deletebutton.clicked.connect(self.removeImage)
        self.editButton.clicked.connect(self._annotateimage)
        self.image.mouseReleaseEvent = self.imageClick
        self.installEventFilter(self)
        self.removeImage()
        self.defaultlocation = ''

    def eventFilter(self, object, event):
        """ Handle mouse click events for disabled widget state """
        if event.type() == QEvent.MouseButtonRelease and not self.isDefault:
            self.openRequest.emit(self.image.pixmap())

        return super(QMapImageWidget, self).eventFilter(object, event)

    def removeImage(self):
        self.loadImage(":/widgets/add", scaled=False)
        self.image.setScaledContents(False)
        self.imageremoved.emit()
        self.isDefault = True

    def imageClick(self, event):
        if self.isDefault:
            self.imageloadrequest.emit()
        else:
            self.openRequest.emit(self.orignalimage)

    def _annotateimage(self):
        self.annotateimage.emit(self.orignalimage)

    @property
    def orignalimage(self):
        if self.isDefault:
            return None
        return self._orignalimage

    def loadImage(self, data, scaled=True, fromfile=True):
        """
            Load the image into the widget using a bytearray

            An empty picture will result in the default placeholder
            image.
        """
        if data is None or not data:
            self.removeImage()
            return

        if fromfile:
            pix = QPixmap(data)
        elif isinstance(data, QPixmap):
            pix = data
        else:
            pix = QPixmap()
            r = pix.loadFromData(data, 'JPG')
            if not r:
                pix = QPixmap(data)

        self._orignalimage = QPixmap(pix)

        h = self.maximumHeight()
        if scaled:
            pix = pix.scaledToHeight(h, Qt.SmoothTransformation)

        self.image.setPixmap(pix)
        self.isDefault = False

    @property
    def isDefault(self):
        return self._isdefault

    @isDefault.setter
    def isDefault(self, value):
        self._isdefault = value
        self.selectbutton.setVisible(not value)
        self.deletebutton.setVisible(not value)
        self.editButton.setVisible(not value)
        if value:
            self.imageloaded.emit()
        else:
            self.imageremoved.emit()

    def getImage(self):
        """ Return the loaded image """
        if self.isDefault:
            return None

        pix = self.orignalimage
        by = QByteArray()
        buf = QBuffer(by)
        buf.open(QIODevice.WriteOnly)
        pix.save(buf, "JPG")
        return by
