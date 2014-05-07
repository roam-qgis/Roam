from PyQt4.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QRectF
from PyQt4.QtGui import  QWidget, QPixmap, QPainter, QLabel, QBrush, QColor, QPen, QTextOption, QFontMetrics

from qgis.core import QgsMapLayer

from roam.ui.uifiles import legend_widget

ICON_SIZE = QSize(32, 32)

OFFSET_X = 30
OFFSET_Y = 40

class LegendWidget(legend_widget, QWidget):
    showmap = pyqtSignal()

    def __init__(self, parent=None):
        super(LegendWidget, self).__init__(parent)
        self.setupUi(self)
        self.pixmap = QPixmap()
        self.items = {}
        self.framerect = QRect()
        self._lastextent = None

        self.legendareabrush = QBrush(QColor(255,255,255,200))
        self.legendareapen = QPen(QColor(255,255,255,20))
        self.legendareapen.setWidth(0.5)

    def paintEvent(self, event):
        def _drawitem(pixmap, text, itempostion):
            painter.drawPixmap(itempostion, pixmap)
            textrect = QRectF(pixmap.width() + OFFSET_Y,
                              itempostion.y(),
                              event.rect().width() - pixmap.width() - OFFSET_X,
                              pixmap.height())
            painter.drawText(textrect, text, QTextOption(Qt.AlignVCenter))

        def calcframewidth(items):
            font = painter.font()
            metrices = QFontMetrics(font)
            maxwidth = 0
            for layer, items in self.items.iteritems():
                if len(items) == 1:
                    maxwidth = max(metrices.boundingRect(layer).width(), maxwidth)
                else:
                    for text, icon in items:
                        maxwidth = max(metrices.boundingRect(text).width(), maxwidth)
            return maxwidth

        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.drawPixmap(event.rect(), self.pixmap)

        rect = event.rect()
        framerect = QRect(rect)
        framewidth = calcframewidth(self.items) + OFFSET_X + ICON_SIZE.width() + 100
        framerect.setWidth(framewidth)
        painter.setBrush(self.legendareabrush)
        painter.setPen(self.legendareapen)
        painter.drawRect(framerect)
        self.framerect = framerect


        painter.setPen(Qt.black)
        currenty = OFFSET_Y
        position = rect.topLeft() + QPoint(OFFSET_X, currenty)
        for layer, items in self.items.iteritems():
            if len(items) == 1:
                itempostion = QPoint(position)
                itempostion.setY(currenty)
                _drawitem(items[0][1], layer, itempostion)
                currenty += OFFSET_Y
            else:
                for text, icon in items:
                    if not text:
                        continue
                    itempostion = QPoint(position)
                    itempostion.setY(currenty)
                    _drawitem(icon, text, itempostion)
                    currenty += OFFSET_Y

            position.setY(currenty + OFFSET_Y)


    def mousePressEvent(self, event):
        if self.framerect.contains(event.pos()):
            return

        self.showmap.emit()


    def updateitems(self, layers):
        self.items = {}
        for layer in layers:
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue

            try:
                items = layer.rendererV2().legendSymbologyItems(ICON_SIZE)
            except AttributeError:
                continue
            self.items[layer.name()] = items
        self.update()

    def updatecanvas(self, canvas):
        """
        Update the canvas object for the legend background.
        """
        if canvas.isDrawing() or self._lastextent == canvas.extent():
            return

        self._lastextent = canvas.extent()
        pixmap = QPixmap(self.size())
        pixmap.fill(canvas.canvasColor())
        painter = QPainter(pixmap)
        painter.setRenderHints(QPainter.Antialiasing)
        renderer = canvas.mapRenderer()
        renderer.render(painter)
        del painter
        self.pixmap = pixmap
        self.update()

