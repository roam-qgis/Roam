from qgis.PyQt.QtCore import pyqtSignal, QSize, Qt
from qgis.PyQt.QtGui import QPixmap, QIcon
from PyQt5.QtMultimedia import QCameraInfo, QCamera, QCameraImageCapture
from PyQt5.QtMultimediaWidgets import QCameraViewfinder
from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QToolBar, QSizePolicy

import roam.config
from roam.editorwidgets.core import LargeEditorWidget
from roam.editorwidgets.imagewidget_utils import stamp_from_config


class CameraError(Exception):
    pass


class _CameraWidget(QWidget):
    imagecaptured = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super(_CameraWidget, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.toolbar = QToolBar()
        spacer = QWidget()
        # spacer.setMinimumWidth(30)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar.setIconSize(QSize(48, 48))
        self.toolbar.addWidget(spacer)
        self.swapaction = self.toolbar.addAction(QIcon(":/widgets/cameraswap"), "Swap Camera")
        self.swapaction.triggered.connect(self.swapcamera)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.toolbar)

        self.current_camera_index = 0
        self.camera = None
        self.viewfinder = QCameraViewfinder()
        self.layout().addWidget(self.viewfinder)
        self.viewfinder.mousePressEvent = self.capture
        self.viewfinder.show()
        self.viewfinder.setAspectRatioMode(Qt.KeepAspectRatioByExpanding)

    def capture(self, *args):
        self.camera.searchAndLock()
        self.camera_capture.capture()
        self.camera.unlock()

    def swapcamera(self):
        cameras = QCameraInfo.availableCameras()
        if self.current_camera_index + 1 == len(cameras):
            self.current_camera_index = 0
        else:
            self.current_camera_index += 1

        self.start(self.current_camera_index)

    @property
    def camera_res(self):
        width, height = tuple(roam.config.settings['camera_res'].split(','))
        return width, height

    def imageCaptured(self, frameid, image):
        # TODO Doing a pixmap convert here is a waste but downstream needs a qpixmap for now
        # refactor later
        self.imagecaptured.emit(QPixmap.fromImage(image))

    def start(self, dev=1):
        if self.camera:
            self.camera.stop()
        cameras = QCameraInfo.availableCameras()
        self.camera = QCamera(cameras[dev])
        self.camera.setViewfinder(self.viewfinder)
        self.camera.setCaptureMode(QCamera.CaptureStillImage)
        self.camera.start()

        self.camera_capture = QCameraImageCapture(self.camera)
        self.camera_capture.setCaptureDestination(QCameraImageCapture.CaptureToBuffer)
        self.camera_capture.imageCaptured.connect(self.imageCaptured)
        # settings = QCameraViewfinderSettings()
        # settings.setResolution(QSize(1280, 720))
        # self.camera.setViewfinderSettings(settings)
        # print(self.camera.supportedViewfinderFrameRateRanges(settings)[0].maximumFrameRate)


class CameraWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(CameraWidget, self).__init__(*args, **kwargs)
        self._value = None

    def createWidget(self, parent):
        return _CameraWidget(parent)

    def initWidget(self, widget, config):
        widget.imagecaptured.connect(self.image_captured)

    def image_captured(self, pixmap):
        image = stamp_from_config(pixmap, self.config)
        self._value = image
        self.emitvaluechanged(self._value)
        self.emit_finished()

    def after_load(self):
        camera = roam.config.settings.get('camera', 0)
        try:
            self.widget.start(dev=camera)
        except CameraError as ex:
            self.emit_cancel(reason=ex.message)
            return

    def value(self):
        return self._value

