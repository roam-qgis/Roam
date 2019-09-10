import os

from qgis.PyQt.QtCore import QByteArray, QVariant, QSize, QDateTime
from qgis.PyQt.QtGui import QPixmap, QIcon
from qgis.PyQt.QtWidgets import QFileDialog, QAction

import roam.api.utils
import roam.config
import roam.resources_rc
from roam import utils
from roam.api import RoamEvents, GPS
from roam.editorwidgets.camerawidget import CameraWidget
from roam.editorwidgets.core import EditorWidget
from roam.editorwidgets.drawingpadwidget import DrawingPadWidget
from roam.editorwidgets.imagewidget_utils import resize_image, save_image
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget
from roam.popupdialogs import PickActionDialog


class ImageWidget(EditorWidget):
    widgettype = 'Image'

    def __init__(self, *args, **kwargs):
        super(ImageWidget, self).__init__(*args)
        self.tobase64 = False
        self.defaultlocation = ''
        self.savetofile = False
        self.filename = None

        self.selectAction = QAction(QIcon(r":\widgets\folder"), "From folder", None)
        self.cameraAction = QAction(QIcon(":\widgets\camera"), "Camera", None)
        self.drawingAction = QAction(QIcon(":\widgets\drawing"), "Drawing/Map snapshot", None)

        self.selectAction.triggered.connect(self._selectImage)
        self.cameraAction.triggered.connect(self._selectCamera)
        self.drawingAction.triggered.connect(self._selectDrawing)
        self.image_size = QSize()
        self.data = {}

    def extraData(self):
        return self.data

    def createWidget(self, parent):
        return QMapImageWidget(parent)

    def initWidget(self, widget, config):
        widget.openRequest.connect(self.showlargeimage)
        widget.imageloaded.connect(self.emitvaluechanged)
        widget.imageremoved.connect(self.emitvaluechanged)
        widget.imageremoved.connect(self.imageremoved)
        widget.imageloadrequest.connect(self.showpicker)
        widget.annotateimage.connect(self._selectDrawing)
        self.image_size = roam.config.read_qsize("image_size")

    def showpicker(self):
        actionpicker = PickActionDialog(msg="Select image source")
        actionpicker.addactions(self.actions)
        actionpicker.exec_()

    def imageremoved(self):
        self.modified = True

    @property
    def actions(self):
        yield self.selectAction
        yield self.cameraAction
        yield self.drawingAction

    def _updateImageGPSData(self):
        # Write to the field with {fieldname}_GPS
        fieldname = self.field.name() + "_GPS"
        if GPS.isConnected:
            location = GPS.latlong_position
            self.data[fieldname] = "{},{}".format(location.x(), location.y())

    def _selectImage(self):
        # Show the file picker
        defaultlocation = os.path.expandvars(self.defaultlocation)
        image = QFileDialog.getOpenFileName(self.widget, "Select Image", defaultlocation)
        utils.debug(image)
        if image is None or not image:
            return

        image = QPixmap(image)
        image = resize_image(image, self.image_size)
        self.setvalue(image)
        self.modified = True
        self._updateImageGPSData()

    def _selectDrawing(self, *args):
        image = self.widget.orignalimage
        self.open_large_widget(DrawingPadWidget, image, self.phototaken, self.config)

    def _selectCamera(self):
        self.open_large_widget(CameraWidget, None, self.phototaken_camera, self.config)

    def phototaken_camera(self, value):
        pix = value.copy()
        pix = resize_image(pix, self.image_size)
        self.setvalue(pix)
        self.modified = True
        self._updateImageGPSData()

    def phototaken(self, value):
        value = resize_image(value, self.image_size)
        self.setvalue(value)
        self.modified = True
        self._updateImageGPSData()

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')
        self.savetofile = self.config.get('savetofile', False)
        if not self.savetofile and self.field and self.field.type() == QVariant.String:
            self.tobase64 = True

    def validate(self, *args):
        return not self.widget.isDefault

    @property
    def saveable(self):
        """
        Is the image saveable by the caller.
        Mainly just a default or Null check so we don't save empty images.
        :return:
        """
        if self.widget.isDefault:
            return False
        return True

    def showlargeimage(self, pixmap):
        RoamEvents.openimage.emit(pixmap)

    def get_filename(self):
        name = QDateTime.currentDateTime().toString("yyyy-MM-dd-hh-mm-ss-zzz.JPG")
        return name

    def save(self, folder, filename):
        if not self.validate():
            return False, None

        value = self.value()
        if not value:
            return

        saved, name = save_image(value, folder, filename)
        return saved

    def setvalue(self, value):
        if self.savetofile and isinstance(value, str):
            self.filename = value

        if isinstance(value, QPixmap):
            self.widget.loadImage(value, fromfile=self.savetofile)
            self.emitvaluechanged()
            return

        if self.tobase64 and value:
            value = QByteArray.fromBase64(value.encode("utf-8"))

        self.widget.loadImage(value, fromfile=self.savetofile)
        self.emitvaluechanged()

    def value(self):
        image = self.widget.getImage()
        if self.tobase64 and image:
            image = image.toBase64()
            return image.data().decode("utf-8")

        return image
