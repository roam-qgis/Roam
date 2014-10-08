import os
import sys

try:
    import vidcap
    from roam.editorwidgets import VideoCapture as vc
    hascamera = True
except ImportError:
    hascamera = False

from PyQt4.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap, QFileDialog, QAction, QToolButton, QIcon, QToolBar
from PyQt4.QtGui import QWidget, QImage
from PyQt4.QtCore import QByteArray, pyqtSignal, QVariant, QTimer, Qt, QSize, QDateTime

from PIL.ImageQt import ImageQt

from roam.editorwidgets.core import EditorWidget, LargeEditorWidget, registerwidgets
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget
from roam.editorwidgets.uifiles import drawingpad
from roam.ui.uifiles import actionpicker_widget, actionpicker_base
from roam.popupdialogs import PickActionDialog
from roam import utils
from roam.api import RoamEvents

import roam.config
import roam.resources_rc


class CameraError(Exception):
    pass


def save_image(image, path, name):
    if isinstance(image, QByteArray):
        _image = QImage()
        _image.loadFromData(image)
        image = _image

    if not os.path.exists(path):
        os.mkdir(path)

    saved = image.save(os.path.join(path, name), "JPG")
    return saved, name

class _CameraWidget(QWidget):
    imagecaptured = pyqtSignal(QPixmap)
    done = pyqtSignal()

    def __init__(self, parent=None):
        super(_CameraWidget, self).__init__(parent)
        self.cameralabel = QLabel()
        self.cameralabel.setScaledContents(True)
        self.setLayout(QGridLayout())
        self.toolbar = QToolBar()
        self.swapaction = self.toolbar.addAction("Swap Camera")
        self.swapaction.triggered.connect(self.swapcamera)
        self.cameralabel.mouseReleaseEvent = self.takeimage
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.cameralabel)
        self.timer = QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.showimage)
        self.cam = None
        self.pixmap = None
        self.currentdevice = 1

    def swapcamera(self):
        self.stop()
        if self.currentdevice == 0:
            self.start(1)
        else:
            self.start(0)

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

    def start(self, dev=1):
        try:
            self.cam = vc.Device(dev)
            self.currentdevice = dev
        except vidcap.error:
            if dev == 0:
                utils.error("Could not start camera")
                raise CameraError("Could not start camera")
            self.start(dev=0)
            return


        roam.config.settings['camera'] = self.currentdevice
        self.timer.start()

    def stop(self):
        self.timer.stop()
        del self.cam
        self.cam = None

class CameraWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(CameraWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return _CameraWidget(parent)

    def initWidget(self, widget):
        widget.imagecaptured.connect(self.emitvaluechanged)
        widget.done.connect(self.emitfished)

    def after_load(self):
        camera = roam.config.settings.get('camera', 1)
        try:
            self.widget.start(dev=camera)
        except CameraError as ex:
            self.emitcancel(reason=ex.message)
            return

    def value(self):
        return self.widget.pixmap

    def __del__(self):
        if self.widget:
            self.widget.stop()



class DrawingPadWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(DrawingPadWidget, self).__init__(*args, **kwargs)
        self.canvas = kwargs.get('map', None)

    def createWidget(self, parent=None):
        pad1 = drawingpad.DrawingPad(parent=parent)
        return pad1

    def initWidget(self, widget):
        widget.actionSave.triggered.connect(self.emitfished)
        widget.actionCancel.triggered.connect(self.emitcancel)
        widget.canvas = self.canvas

    def value(self):
        return self.widget.pixmap

    def setvalue(self, value):
        self.widget.pixmap = value


class ImageWidget(EditorWidget):
    widgettype = 'Image'

    def __init__(self, *args):
        super(ImageWidget, self).__init__(*args)
        self.tobase64 = False
        self.defaultlocation = ''
        self.savetofile= False
        self.modified = False
        self.filename = None

        self.selectAction = QAction(QIcon(r":\widgets\folder"), "From folder", None)
        self.cameraAction = QAction(QIcon(":\widgets\camera"), "Camera", None)
        self.drawingAction = QAction(QIcon(":\widgets\drawing"), "Drawing", None)

        self.selectAction.triggered.connect(self._selectImage)
        self.cameraAction.triggered.connect(self._selectCamera)
        self.drawingAction.triggered.connect(self._selectDrawing)


    def createWidget(self, parent):
        return QMapImageWidget(parent)

    def initWidget(self, widget):
        widget.openRequest.connect(self.showlargeimage)
        widget.imageloaded.connect(self.emitvaluechanged)
        widget.imageremoved.connect(self.emitvaluechanged)
        widget.imageloadrequest.connect(self.showpicker)
        widget.annotateimage.connect(self._selectDrawing)

    def showpicker(self):
        actionpicker = PickActionDialog(msg="Select image source")
        actionpicker.addactions(self.actions)
        actionpicker.exec_()

    @property
    def actions(self):
        yield self.selectAction
        if hascamera:
            yield self.cameraAction
        yield self.drawingAction

    def _selectImage(self):
        # Show the file picker
        defaultlocation = os.path.expandvars(self.defaultlocation)
        image = QFileDialog.getOpenFileName(self.widget, "Select Image", defaultlocation)
        utils.debug(image)
        if image is None or not image:
            return

        self.widget.loadImage(image)
        self.modified = True

    def _selectDrawing(self, *args):
        image = self.widget.orignalimage
        self.largewidgetrequest.emit(DrawingPadWidget, image, self.phototaken, {})

    def _selectCamera(self):
        self.largewidgetrequest.emit(CameraWidget, None, self.phototaken, {})

    def phototaken(self, value):
        self.setvalue(value)
        self.modified = True

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')
        self.savetofile = self.config.get('savetofile', False)
        if not self.savetofile and self.field and self.field.type() == QVariant.String:
            self.tobase64 = True

    def validate(self, *args):
        return not self.widget.isDefault

    def showlargeimage(self, pixmap):
        RoamEvents.openimage.emit(pixmap)

    def get_filename(self):
        name = QDateTime.currentDateTime().toString("yyyy-MM-dd-hh-mm-ss.JPG")
        return name

    def save(self, folder, filename):
        saved, name = save_image(self.widget.getImage(), folder, filename)
        return saved

    def setvalue(self, value):
        if self.savetofile and isinstance(value, basestring):
            self.filename = value

        if isinstance(value, QPixmap):
            self.widget.loadImage(value, fromfile=self.savetofile)
            return

        if self.tobase64 and value:
            value = QByteArray.fromBase64(value)

        self.widget.loadImage(value, fromfile=self.savetofile)

    def value(self):
        image = self.widget.getImage()
        if self.tobase64 and image:
            image = image.toBase64()
            return image.data()

        return image

