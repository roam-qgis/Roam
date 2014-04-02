import os.path
import functools

from PyQt4 import QtCore, QtGui

from PyQt4.QtGui import QWidget, QPixmap, QPainter

from roam.editorwidgets.uifiles.ui_drawingpad import Ui_DrawingWindow


class ScribbleArea(QWidget):
    def __init__(self, parent=None):
        super(ScribbleArea, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        self.modified = False
        self.scribbling = False
        imageSize = QtCore.QSize(500, 500)
        self.image = QtGui.QImage(imageSize, QtGui.QImage.Format_RGB16)
        self.lastPoint = QtCore.QPoint()

    def openImage(self, fileName):
        loadedImage = QtGui.QImage()
        if not loadedImage.load(fileName):
            return False
        
        self.image = loadedImage
        self.modified = False
        self.update()
        return True

    def saveImage(self, fileName, fileFormat):
        visibleImage = self.image
        self.resizeImage(visibleImage, self.size())

        path = os.path.dirname(fileName)

        if not os.path.exists(path):
            os.makedirs(path)
            
        if visibleImage.save(fileName, fileFormat):
            self.modified = False
            log("Saved")
            return True
        else:
            log("Didn't save")
            return False

    def setPenColor(self, newColor):
        self.myPenColor = newColor

    def setPenWidth(self, newWidth):
        self.myPenWidth = newWidth

    def clearImage(self):
        self.image.fill(QtGui.qRgb(255, 255, 255))
        self.modified = True
        self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.lastPoint = event.pos()
            self.scribbling = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & QtCore.Qt.LeftButton) and self.scribbling:
            self.drawLineTo(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.scribbling:
            self.drawLineTo(event.pos())
            self.scribbling = False

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(event.rect(), self.image)

    def addMap(self, pixmap):
        painter = QtGui.QPainter(self.image)
        painter.drawPixmap(QtCore.QPoint(0,0), pixmap)
        self.update()

    def resizeEvent(self, event):
        self.resizeImage(self.image, event.size())
        super(ScribbleArea, self).resizeEvent(event)

    def drawLineTo(self, endPoint):
        painter = QtGui.QPainter(self.image)
        painter.setPen(QtGui.QPen(self.myPenColor, self.myPenWidth,
            QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.drawLine(self.lastPoint, endPoint)
        self.modified = True
        self.update()
        self.lastPoint = QtCore.QPoint(endPoint)

    def resizeImage(self, image, newSize):
        if image.size() == newSize:
            return

        # this resizes the canvas without resampling the image
        newImage = QtGui.QImage(newSize, QtGui.QImage.Format_RGB32)
        newImage.fill(QtGui.qRgb(255, 255, 255))
        painter = QtGui.QPainter(newImage)
        painter.drawImage(QtCore.QPoint(0, 0), image)

        self.image = newImage

    @property
    def pixmap(self):
        return QPixmap.fromImage(self.image)

    def isModified(self):
        return self.modified

    def penColor(self):
        return self.myPenColor

    def penWidth(self):
        return self.myPenWidth


class DrawingPad(Ui_DrawingWindow, QWidget):
    def __init__(self, startimage=None, parent=None):
        super(DrawingPad, self).__init__(parent)
        self.saveAsActs = []
        
        self.setupUi(self)

        self.scribbleArea = ScribbleArea()
        self.scribbleArea.clearImage()
    
        self.frame.layout().addWidget(self.scribbleArea)
        self.createActions()

        self.actionRedPen.trigger()

        self.setWindowTitle("Scribble")
        self.resize(500, 500)

        self.openImage(startimage)

        self.canvas = None

    @property
    def canvas(self):
        return self._canvas

    @canvas.setter
    def canvas(self, value):
        enabled = True if value else False
        self.actionMapSnapshot.setEnabled(enabled)
        self._canvas = value

    @property
    def pixmap(self):
        return self.scribbleArea.pixmap

    def getmap(self):
        if self.canvas:
            painter = QPainter()
            pixmap = QPixmap(self.canvas.size())
            painter.begin(pixmap)
            renderer = self.canvas.mapRenderer()
            renderer.render(painter)
            self.scribbleArea.addMap(pixmap)

    def openImage(self, image):
        if not image is None and os.path.exists(image):
            self.scribbleArea.openImage(image)

    def saveImage(self, filename):
        filename = filename + ".png"
        log(filename)
        return self.scribbleArea.saveImage(filename, "png")

    def setPen(self, color, size=3):
        self.scribbleArea.setPenWidth(size)
        self.scribbleArea.setPenColor(color)

    def createActions(self):
        self.actionClearDrawing.triggered.connect(self.scribbleArea.clearImage)
        self.toolClear.setDefaultAction(self.actionClearDrawing)

        self.actionRedPen.triggered.connect(functools.partial(self.setPen, QtCore.Qt.red, 3))
        self.toolRedPen.setDefaultAction(self.actionRedPen)

        self.actionBluePen.triggered.connect(functools.partial(self.setPen, QtCore.Qt.blue, 3))
        self.toolBluePen.setDefaultAction(self.actionBluePen)

        self.actionBlackPen.triggered.connect(functools.partial(self.setPen, QtCore.Qt.black, 3))
        self.toolBlackPen.setDefaultAction(self.actionBlackPen)

        self.actionEraser.triggered.connect(functools.partial(self.setPen, QtCore.Qt.white, 9))
        self.toolEraser.setDefaultAction(self.actionEraser)

        self.actionMapSnapshot.triggered.connect(self.getmap)
        self.toolMapSnapshot.setDefaultAction(self.actionMapSnapshot)

        self.toolSave.setDefaultAction(self.actionSave)
        self.toolCancel.setDefaultAction(self.actionCancel)



if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    window = DrawingPad()
    window.show()
    sys.exit(app.exec_())
