import os.path
from ui_drawingpad import Ui_DrawingWindow
from PyQt4 import QtCore, QtGui
import functools
from utils import log

class ScribbleArea(QtGui.QWidget):
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

    def isModified(self):
        return self.modified

    def penColor(self):
        return self.myPenColor

    def penWidth(self):
        return self.myPenWidth

class DrawingPad(QtGui.QDialog):
    def __init__(self, startimage=None):
        QtGui.QDialog.__init__(self)
        self.saveAsActs = []
        
        self.ui = Ui_DrawingWindow()
        self.ui.setupUi(self)

        self.scribbleArea = ScribbleArea()
        self.scribbleArea.clearImage()
    
        self.ui.frame.layout().addWidget(self.scribbleArea)
        self.createActions()

        self.ui.actionRedPen.trigger()

        self.setWindowTitle("Scribble")
        self.resize(500, 500)

        if not startimage is None and os.path.exists(startimage):
            self.openImage(startimage)

    def saveImage(self, filename):
        filename = filename + ".jpg"
        log(filename)
        return self.scribbleArea.saveImage(filename, "jpg")

    def setPen(self, color, size=3):
        self.scribbleArea.setPenWidth(size)
        self.scribbleArea.setPenColor(color)

    def createActions(self):
        self.ui.actionClearDrawing.triggered.connect(self.scribbleArea.clearImage)
        self.ui.toolClear.setDefaultAction(self.ui.actionClearDrawing)
        
        self.ui.actionRedPen.triggered.connect(functools.partial(self.setPen, QtCore.Qt.red, 3))
        self.ui.toolRedPen.setDefaultAction(self.ui.actionRedPen)

        self.ui.actionBluePen.triggered.connect(functools.partial(self.setPen, QtCore.Qt.blue, 3))
        self.ui.toolBluePen.setDefaultAction(self.ui.actionBluePen)

        self.ui.actionBlackPen.triggered.connect(functools.partial(self.setPen, QtCore.Qt.black, 3))
        self.ui.toolBlackPen.setDefaultAction(self.ui.actionBlackPen)

        self.ui.actionEraser.triggered.connect(functools.partial(self.setPen, QtCore.Qt.white, 9))
        self.ui.toolEraser.setDefaultAction(self.ui.actionEraser)

        self.ui.toolMapSnapshot.setDefaultAction(self.ui.actionMapSnapshot)

        self.ui.toolSave.setDefaultAction(self.ui.actionSave)
        self.ui.toolCancel.setDefaultAction(self.ui.actionCancel)

    def openImage(self,image):
        self.scribbleArea.openImage(image)
        
if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    window = DrawingPad()
    window.show()
    sys.exit(app.exec_())
