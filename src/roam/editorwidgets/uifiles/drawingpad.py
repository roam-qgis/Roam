import os.path
import functools

from PyQt4 import QtCore, QtGui

from PyQt4.QtGui import QWidget, QPixmap, QPainter, QColorDialog
from PyQt4.QtCore import Qt
from qgis.core import QGis

from roam.editorwidgets.uifiles.ui_drawingpad import Ui_DrawingWindow


class ScribbleArea(QWidget):
    def __init__(self, parent=None):
        super(ScribbleArea, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        self.modified = False
        self.scribbling = False
        imageSize = QtCore.QSize(500, 500)
        self.image = QtGui.QImage(imageSize, QtGui.QImage.Format_RGB16)
        self.userimage = None
        self.painter = QtGui.QPainter()
        self.lastPoint = QtCore.QPoint()
        self.pen = QtGui.QPen()

    def setPenColor(self, newColor):
        self.myPenColor = newColor
        self.pen.setColor(newColor)

    def setPenWidth(self, newWidth):
        self.myPenWidth = newWidth
        self.pen.setWidth(newWidth)

    def penColor(self):
        return self.myPenColor

    def penWidth(self):
        return self.myPenWidth

    def clearImage(self):
        self.image.fill(QtGui.qRgb(255, 255, 255))
        self.modified = True
        self.update()

    def mousePressEvent(self, event):
        self.painter.begin(self.image)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
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
        self.painter.end()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(event.rect(), self.image)
        del painter

    def addMapImage(self, image):
        self.painter.begin(self.image)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.drawImage(QtCore.QPoint(0,0), image)
        self.painter.end()
        self.update()

    def addMap(self, pixmap):
        self.painter.begin(self.image)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.drawPixmap(QtCore.QPoint(0,0), pixmap)
        self.painter.end()
        self.update()

    def resizeEvent(self, event):
        #self.resizeImage(self.image, event.size())
        super(ScribbleArea, self).resizeEvent(event)

    def drawLineTo(self, endPoint):
        self.painter.setPen(self.pen)
        self.painter.drawLine(self.lastPoint, endPoint)
        self.lastPoint = QtCore.QPoint(endPoint)
        self.modified = True
        self.update()

    def showEvent(self, event):
        newImage = QtGui.QImage(self.size(), QtGui.QImage.Format_RGB32)
        newImage.fill(QtGui.qRgb(255, 255, 255))
        self.image = newImage
        if self.userimage:
            self.addMap(self.userimage)

    def resizeImage(self, image, newSize):
        if image.size() == newSize:
            return

        newImage = self.image.scaled(newSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image = newImage
        self.update()

    @property
    def pixmap(self):
        return QPixmap.fromImage(self.image)

    @pixmap.setter
    def pixmap(self, value):
        self.userimage = value
        #if value:
        #    self.addMap(value)

    def isModified(self):
        return self.modified



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
        self.colorPickerButton.clicked.connect(self.pickcolour)

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

    @pixmap.setter
    def pixmap(self, value):
        self.scribbleArea.pixmap = value

    def pickcolour(self):
        colour = QColorDialog.getColor(Qt.black, self)
        self.scribbleArea.setPenColor(colour)

    def rendermap(self):
        image = self.renderjob.renderedImage()
        self.scribbleArea.addMapImage(image)

    def getmap(self):
        if self.canvas:
            if QGis.QGIS_VERSION_INT > 20200:
                from qgis.core import QgsMapRendererParallelJob
                self.renderjob = QgsMapRendererParallelJob(self.canvas.mapSettings())
                self.renderjob.finished.connect(self.rendermap)
                self.renderjob.start()
            else:
                pixmap = QPixmap(self.canvas.size())
                pixmap.fill(self.canvas.canvasColor())
                painter = QPainter(pixmap)
                renderer = self.canvas.mapRenderer()
                renderer.render(painter)
                del painter
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
