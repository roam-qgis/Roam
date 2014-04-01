import os
import sys

try:
    import VideoCapture as vc
    hascamera = True
except ImportError:
    hascamera = False

from PyQt4.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap, QFileDialog, QAction, QToolButton, QIcon, QToolBar
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import QByteArray, pyqtSignal, QVariant, QTimer, Qt, QSize

from PIL.ImageQt import ImageQt

from roam.editorwidgets.core import EditorWidget, LargeEditorWidget
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget
from roam.ui.uifiles import actionpicker_widget, actionpicker_base
from roam.popupdialogs import PickActionDialog
from roam import utils

import roam.editorwidgets.uifiles.images_rc

class _CameraWidget(QWidget):
    imagecaptured = pyqtSignal(QPixmap)
    done = pyqtSignal()

    def __init__(self, parent=None):
        super(_CameraWidget, self).__init__(parent)
        self.cameralabel = QLabel()
        self.cameralabel.setScaledContents(True)
        self.setLayout(QGridLayout())
        self.cameralabel.mouseReleaseEvent = self.takeimage
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self.cameralabel)
        self.timer = QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.showimage)
        self.cam = None
        self.imagecaptured.connect(self.printvalue)

    def printvalue(self, value):
        print value

    def showimage(self):
        if self.cam is None:
            return

        img = self.cam.getImage()
        self.image = ImageQt(img)
        pixmap = QPixmap.fromImage(self.image)
        self.cameralabel.setPixmap(pixmap)

    def takeimage(self, *args):
        self.timer.stop()

        img = self.cam.getImage()
        self.image = ImageQt(img)
        self.pixmap = QPixmap.fromImage(self.image)
        self.cameralabel.setPixmap(self.pixmap)
        self.imagecaptured.emit(self.pixmap)
        self.done.emit()

    def start(self):
        self.cam = vc.Device()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        del self.cam
        self.cam = None

class CameraWidget(LargeEditorWidget):
    def __init__(self, *args):
        super(CameraWidget, self).__init__(*args)

    def createWidget(self, parent):
        return _CameraWidget(parent)

    def initWidget(self, widget):
        widget.imagecaptured.connect(self.emitvaluechanged)
        widget.done.connect(self.emitfished)
        widget.start()

    def value(self):
        return self.widget.pixmap

    def __del__(self):
        if self.widget:
            self.widget.stop()


class ImageWidget(EditorWidget):
    widgettype = 'Image'
    openimage = pyqtSignal(object)

    def __init__(self, *args):
        super(ImageWidget, self).__init__(*args)
        self.tobase64 = False
        self.defaultlocation = ''

        self.selectAction = QAction(QIcon(r":\images\folder"), "From folder", None)
        self.cameraAction = QAction(QIcon(":\images\camera"), "Camera", None)

        self.selectAction.triggered.connect(self._selectImage)
        self.cameraAction.triggered.connect(self._selectCamera)

        if self.field and self.field.type() == QVariant.String:
            self.tobase64 = True

    def createWidget(self, parent):
        return QMapImageWidget(parent)

    def initWidget(self, widget):
        widget.openRequest.connect(self.showlargeimage)
        widget.imageloaded.connect(self.validate)
        widget.imageremoved.connect(self.validate)
        widget.imageloadrequest.connect(self.showpicker)

    def showpicker(self):
        actionpicker = PickActionDialog(msg="Select image source")
        actionpicker.addactions(self.actions)
        actionpicker.exec_()

    @property
    def actions(self):
        yield self.selectAction
        if hascamera:
            yield self.cameraAction

    def _selectImage(self):
        # Show the file picker
        defaultlocation = os.path.expandvars(self.defaultlocation)
        image = QFileDialog.getOpenFileName(self.widget, "Select Image", defaultlocation)
        utils.debug(image)
        if image is None or not image:
            return

        self.widget.loadImage(image)

    def _selectCamera(self):
        self.largewidgetrequest.emit(CameraWidget, self.phototaken)

    def phototaken(self, value):
        self.setvalue(value)

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')

    def validate(self, *args):
        self.raisevalidationupdate(not self.widget.isDefault)
        self.emitvaluechanged()

    def showlargeimage(self, pixmap):
        self.openimage.emit(pixmap)

    def setvalue(self, value):
        if self.tobase64 and value and not isinstance(value, QPixmap):
            value = QByteArray.fromBase64(value)

        self.widget.loadImage(value)

    def value(self):
        image = self.widget.getImage()
        if self.tobase64 and image:
            image = image.toBase64()
            return image.data()

        return image

