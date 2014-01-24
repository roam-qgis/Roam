from PyQt4.QtCore import Qt
from roam.ui.uifiles import imageviewer_widget, imageviewer_base


class ImageViewer(imageviewer_widget, imageviewer_base):
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self.setupUi(self)
        self.imagelabel.mouseReleaseEvent = lambda x: self.hide()

    def openimage(self, pixmap):
        self.show()
        pix = pixmap.scaledToHeight(self.imagelabel.height(), Qt.SmoothTransformation)
        self.imagelabel.setPixmap(pix)
