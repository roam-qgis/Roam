import tempfile
import os

from PyQt4.QtGui import QDesktopServices, QImage
from PyQt4.QtCore import Qt, QUrl
from roam.ui.uifiles import imageviewer_widget, imageviewer_base


class ImageViewer(imageviewer_widget, imageviewer_base):
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self.setupUi(self)
        self.image = QImage()
        self.imagelabel.mouseReleaseEvent = lambda x: self.hide()
        self.btnOpenImage.clicked.connect(self.open_in_external)

    def openimage(self, pixmap):
        self.show()
        self.image = pixmap.toImage()
        pix = pixmap.scaledToHeight(self.imagelabel.height(), Qt.SmoothTransformation)
        self.imagelabel.setPixmap(pix)

    def open_in_external(self):
        newfile = os.path.join(tempfile.tempdir, "roam_temp.jpg")
        self.image.save(newfile)
        QDesktopServices.openUrl(QUrl.fromLocalFile(newfile))
