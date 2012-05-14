from ui_drawingpad import Ui_DrawingWindow
from PyQt4 import QtCore, QtGui
import functools

class ScribbleArea(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ScribbleArea, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        self.modified = False
        self.scribbling = False
        self.myPenWidth = 1
        self.myPenColor = QtCore.Qt.blue
        imageSize = QtCore.QSize(500, 500)
        self.image = QtGui.QImage(imageSize, QtGui.QImage.Format_RGB32)
        self.lastPoint = QtCore.QPoint()

    def openImage(self, fileName):
        loadedImage = QtGui.QImage()
        if not loadedImage.load(fileName):
            return False

        w = loadedImage.width()
        h = loadedImage.height()
        self.mainWindow.resize(w, h)

        self.image = loadedImage
        self.modified = False
        self.update()
        return True

    def saveImage(self, fileName, fileFormat):
        visibleImage = self.image
        self.resizeImage(visibleImage, self.size())

        if visibleImage.save(fileName, fileFormat):
            self.modified = False
            return True
        else:
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
        print "Resize"
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

    def print_(self):
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printDialog = QtGui.QPrintDialog(printer, self)
        if printDialog.exec_() == QtGui.QDialog.Accepted:
            painter = QtGui.QPainter(printer)
            rect = painter.viewport()
            size = self.image.size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.image.rect())
            painter.drawImage(0, 0, self.image)
            painter.end()

    def isModified(self):
        return self.modified

    def penColor(self):
        return self.myPenColor

    def penWidth(self):
        return self.myPenWidth

class DrawingPad(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.saveAsActs = []
        
        self.ui = Ui_DrawingWindow()
        self.ui.setupUi(self)

        self.scribbleArea = ScribbleArea(self)
        self.scribbleArea.clearImage()
        self.scribbleArea.mainWindow = self
        self.setCentralWidget(self.scribbleArea)
        
        self.scribbleArea.setPenWidth(3)

        self.createActions()

        self.setWindowTitle("Scribble")
        self.resize(500, 500)

    def save(self):
        action = self.sender()
        fileFormat = action.data()
        self.saveFile(fileFormat)

    def setPenColor(self, color):
        self.scribbleArea.setPenColor(color)

    def createActions(self):
        spacewidget = QtGui.QWidget()
        spacewidget.setMinimumWidth(30)
        spacewidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        
        autospacewidget = QtGui.QWidget()
        autospacewidget.setMinimumWidth(30)
        autospacewidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        self.ui.actionClearDrawing.triggered.connect(self.scribbleArea.clearImage)
        self.ui.actionRedPen.triggered.connect(functools.partial(self.scribbleArea.setPenColor, QtCore.Qt.red))
        self.ui.actionBluePen.triggered.connect(functools.partial(self.scribbleArea.setPenColor, QtCore.Qt.blue))
        self.ui.actionBlackPen.triggered.connect(functools.partial(self.scribbleArea.setPenColor, QtCore.Qt.black))

        self.ui.toolBar.insertWidget(self.ui.actionRedPen, spacewidget)
        self.ui.toolBar.insertWidget(self.ui.actionSave, autospacewidget)

    def saveFile(self, fileFormat):
        initialPath = QtCore.QDir.currentPath() + '/untitled.' + fileFormat

        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save As",
            initialPath,
            "%s Files (*.%s);;All Files (*)" % (fileFormat.upper(), fileFormat))
        if fileName:
            return self.scribbleArea.saveImage(fileName, fileFormat)

        return False

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    window = DrawingPad()
    window.showFullScreen()
    sys.exit(app.exec_())
