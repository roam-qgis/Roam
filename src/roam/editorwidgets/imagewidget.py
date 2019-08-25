import os
import sys
import uuid
import functools
import sqlite3

try:
    import vidcap
    from roam.editorwidgets import VideoCapture as vc

    hascamera = True
except ImportError:
    hascamera = False

from PyQt5.QtGui import QDialog, QGridLayout, QLabel, QLayout, QPixmap, QFileDialog, QAction, QToolButton, QIcon, \
    QToolBar, QPainter, QPen
from PyQt5.QtGui import QWidget, QImage, QSizePolicy, QTextDocument, QVBoxLayout
from PyQt5.QtCore import QByteArray, pyqtSignal, QVariant, QTimer, Qt, QSize, QDateTime, QPointF

from qgis.core import QgsExpression
from PIL.ImageQt import ImageQt

from roam.editorwidgets.core import EditorWidget, LargeEditorWidget, registerwidgets, createwidget, widgetwrapper
from roam.editorwidgets.uifiles.imagewidget import QMapImageWidget
from roam.editorwidgets.uifiles import drawingpad
from roam.ui.uifiles import actionpicker_widget, actionpicker_base
from roam.popupdialogs import PickActionDialog
from roam import utils
from roam.api import RoamEvents, GPS
from roam.dataaccess.database import Database, DatabaseException

import roam.config
import roam.resources_rc


class CameraError(Exception):
    pass


def stamp_from_config(image, config):
    stamp = config.get('stamp', None)
    form = config.get('formwidget', None)
    feature = None
    if not stamp:
        return image

    if form:
        feature = form.to_feature()
    image = stamp_image(image, stamp['value'], stamp['position'], feature)
    return image


def stamp_image(image, expression_str, position, feature):
    painter = QPainter(image)
    data = QgsExpression.replaceExpressionText(expression_str, feature, None)
    if not data:
        return image

    data = data.replace(r"\n", "<br>")
    style = """
    body {
        color: yellow;
    }
    """
    doc = QTextDocument()
    doc.setDefaultStyleSheet(style)
    data = "<body>{}</body>".format(data)
    doc.setHtml(data)
    point = QPointF(20, 20)

    # Wrap the text so we don't go crazy
    if doc.size().width() > 300:
        doc.setTextWidth(300)
    if position == "top-left":
        point = QPointF(20, 20)
    elif position == "top-right":
        x = image.width() - 20 - doc.size().width()
        point = QPointF(x, 20)
    elif position == "bottom-left":
        point = QPointF(20, image.height() - 20 - doc.size().height())
    elif position == "bottom-right":
        x = image.width() - 20 - doc.size().width()
        y = image.height() - 20 - doc.size().height()
        point = QPointF(x, y)
    painter.translate(point)
    doc.drawContents(painter)
    return image


def resize_image(image, size):
    """
    Resize the given image to the given size.  Doesn't resize if smaller.
    :param image: a QImage to resize.
    :param size: The QSize of the result image. Will not resize if image is smaller.
    :return: The new sized image.
    """
    if size and not size.isEmpty() and image.width() > size.width() and image.height() > size.height():
        return image.scaled(size, Qt.KeepAspectRatio)
    else:
        return image


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
        spacer = QWidget()
        # spacer.setMinimumWidth(30)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar.setIconSize(QSize(48, 48))
        self.toolbar.addWidget(spacer)
        self.swapaction = self.toolbar.addAction(QIcon(":/widgets/cameraswap"), "Swap Camera")
        self.swapaction.triggered.connect(self.swapcamera)
        self.cameralabel.mouseReleaseEvent = self.takeimage
        self.layout().setContentsMargins(0, 0, 0, 0)
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

    @property
    def camera_res(self):
        width, height = tuple(roam.config.settings['camera_res'].split(','))
        return width, height

    def start(self, dev=1):
        try:
            self.cam = vc.Device(dev)
            try:
                width, height = self.camera_res
                self.cam.setResolution(int(width), int(height))
            except KeyError:
                pass
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
        self._value = None

    def createWidget(self, parent):
        return _CameraWidget(parent)

    def initWidget(self, widget, config):
        widget.imagecaptured.connect(self.image_captured)
        widget.done.connect(self.emit_finished)

    def image_captured(self, pixmap):
        image = stamp_from_config(pixmap, self.config)
        self._value = image
        self.emitvaluechanged(self._value)

    def after_load(self):
        camera = roam.config.settings.get('camera', 1)
        try:
            self.widget.start(dev=camera)
        except CameraError as ex:
            self.emit_cancel(reason=ex.message)
            return

    def value(self):
        return self._value

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

    def initWidget(self, widget, config):
        widget.toolStamp.pressed.connect(self.stamp_image)
        widget.actionSave.triggered.connect(self.emit_finished)
        widget.actionCancel.triggered.connect(self.emit_cancel)
        widget.canvas = self.canvas

    def stamp_image(self):
        image = self.widget.pixmap
        image = stamp_from_config(image, self.config)
        self.widget.pixmap = image

    def value(self):
        return self.widget.pixmap

    def setvalue(self, value):
        self.widget.pixmap = value


class MultiImageWidget(EditorWidget):
    widgettype = 'MultiImage'

    def __init__(self, *args, **kwargs):
        super(MultiImageWidget, self).__init__(*args, **kwargs)
        self.widgets = []
        self.linkid = None
        self.modified = True

    def createWidget(self, parent=None):
        widget = QWidget(parent)
        return widget

    def initWidget(self, widget, config):
        if not widget.layout():
            widget.setLayout(QVBoxLayout())
            widget.layout().setContentsMargins(0, 0, 0, 0)

        dbconfig = config['dboptions']
        for i in xrange(dbconfig['maximages']):
            innerwidget = createwidget("Image")
            wrapper = widgetwrapper("Image", innerwidget, config, self.layer, self.label, self.field, self.context)
            wrapper.largewidgetrequest.connect(self.largewidgetrequest.emit)
            wrapper.photo_id = None
            wrapper.photo_number = i
            widget.layout().addWidget(innerwidget)
            self.widgets.append((innerwidget, wrapper))

    def setvalue(self, value):
        """
        The multi image widget will take the ID to lookup in the external DB.
        """
        import uuid

        if not value:
            self.linkid = str(uuid.uuid4())
        else:
            self.linkid = value

        table = self.DBConfig['table']
        db = self.DB()
        photos = db.execute("""
        SELECT photo_id, photo
        FROM '{0}'
        WHERE linkid = '{1}'
        ORDER BY photo_number
        """.format(table, self.linkid))
        for count, row in enumerate(photos):
            try:
                widget, wrapper = self.widgets[count]
                data = row[1]
                photo_id = row[0]
                wrapper.photo_id = photo_id
                wrapper.setvalue(data)
            except IndexError:
                break

        db.close()

    def value(self):
        """
        The current ID of the image link.
        """
        if not self.linkid:
            self.linkid = str(uuid.uuid4())

        return self.linkid

    def updatePhoto(self, db, photo_id, photo):
        table = self.DBConfig['table']
        sql = """UPDATE '{0}' SET photo = '{2}',
                                  timestamp = '{4}'
                                  WHERE photo_id = '{3}'
                                  AND linkid = '{1}'""".format(table,
                                                               self.linkid,
                                                               photo,
                                                               photo_id,
                                                               QDateTime.currentDateTime().toLocalTime().toString())
        db.execute(sql)

    def DB(self):
        dbconfig = self.config['dboptions']
        dbpath = dbconfig['dbpath']
        dbpath = os.path.join(self.config['context']['project'].datafolder(), dbpath)
        table = dbconfig['table']
        db = sqlite3.connect(dbpath)
        db.enable_load_extension(True)
        db.load_extension("spatialite4.dll")
        return db

    @property
    def DBConfig(self):
        dbconfig = self.config['dboptions']
        return dbconfig

    def insertPhoto(self, db, photo_id, photo, number):
        table = self.DBConfig['table']
        linkcode = self.DBConfig['linkcode']
        date = QDateTime.currentDateTime().toLocalTime().toString()
        sql = "INSERT INTO '{0}' (linkid, photo, photo_id, timestamp, photo_number, linkname) VALUES ('{1}', '{2}', '{3}', '{4}', {5}, '{6}')".format(
            table, self.linkid, photo, photo_id, date, number, linkcode)
        db.execute(sql)

    def save(self):
        """
        Save the images inside this widget to the linked DB.
        """
        db = self.DB()
        for widget, wrapper in self.widgets:
            value = wrapper.value()
            if not wrapper.modified:
                continue

            if wrapper.photo_id is None:
                if value:
                    wrapper.photo_id = str(uuid.uuid4())
                    self.insertPhoto(db, wrapper.photo_id, value, wrapper.photo_number)
            else:
                if not value:
                    value = ''
                self.updatePhoto(db, wrapper.photo_id, value)
        db.commit()
        db.close()
        return True


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
        if hascamera:
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
        if self.savetofile and isinstance(value, basestring):
            self.filename = value

        if isinstance(value, QPixmap):
            self.widget.loadImage(value, fromfile=self.savetofile)
            self.emitvaluechanged()
            return

        if self.tobase64 and value:
            value = QByteArray.fromBase64(value)

        self.widget.loadImage(value, fromfile=self.savetofile)
        self.emitvaluechanged()

    def value(self):
        image = self.widget.getImage()
        if self.tobase64 and image:
            image = image.toBase64()
            return image.data()

        return image
