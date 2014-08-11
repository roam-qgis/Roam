import math
from PyQt4.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QRectF
from PyQt4.QtGui import  QIcon, QWidget, QPixmap, QPainter, QLabel, QBrush, QColor, QPen, QTextOption, QFontMetrics

from qgis.core import QgsMapLayer

from roam.ui.uifiles import legend_widget
from roam.api import plugins

ICON_SIZE = QSize(32, 32)


@plugins.page(name='Legend', title='Legend', icon=QIcon(r':/icons/legend'), projectpage=True)
class LegendWidget(legend_widget, QWidget):
    def __init__(self, api, parent=None):
        super(LegendWidget, self).__init__(parent)
        self.setupUi(self)
        self.pixmap = QPixmap()
        self.items = {}
        self.framerect = QRect()
        self._lastextent = None
        self.api = api

        self.legendareabrush = QBrush(QColor(255,255,255,200))
        self.legendareapen = QPen(QColor(255,255,255,20))
        self.legendareapen.setWidth(0.5)

        self.api.events.projectloaded.connect(self.projectloaded)

    def projectloaded(self, project):
        layers = project.legendlayersmapping().values()
        self.updateitems(layers)

    def showEvent(self, QShowEvent):
        self.updatecanvas(self.api.canvas)

    def paintEvent(self, event):
        def itemlist():
            for layer, items in self.items.iteritems():
                if len(items) == 1:
                    yield layer, items[0][1]
                else:
                    for text, icon in items:
                        if not text:
                            continue
                        yield text, icon

        def _drawitem(pixmap, text, itempostion):
            painter.drawPixmap(itempostion, pixmap)
            textrect = QRectF(pixmap.width() + currentx + 10,
                              itempostion.y(),
                              event.rect().width() - pixmap.width() - OFFSET_X,
                              pixmap.height())
            painter.drawText(textrect, text, QTextOption(Qt.AlignVCenter))

        def calcitems():
            font = painter.font()
            metrices = QFontMetrics(font)
            maxwidth = 0
            maxheight = 0
            for item, _ in itemlist():
                maxwidth = max(metrices.boundingRect(item).width(), maxwidth)
                maxheight = max(metrices.boundingRect(item).height(), maxheight)
            return maxwidth, maxheight

        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.drawPixmap(event.rect(), self.pixmap)

        itemwidths, itemmaxheight = calcitems()
        OFFSET_X = 30
        OFFSET_Y = itemmaxheight + 10
        rect = event.rect()
        neededheight = (len(self.items) * OFFSET_Y)
        columns = 1
        if neededheight > rect.height():
            columns = math.ceil(neededheight / float(rect.height()))

        framerect = QRect(rect)
        framewidth = (itemwidths + OFFSET_X + ICON_SIZE.width() + 100) * columns
        framerect.setWidth(framewidth)
        painter.setBrush(self.legendareabrush)
        painter.setPen(self.legendareapen)
        painter.drawRect(framerect)
        self.framerect = framerect

        painter.setPen(Qt.black)
        currenty = OFFSET_Y
        currentx = OFFSET_X
        position = rect.topLeft() + QPoint(OFFSET_X, currenty)
        for text, icon in itemlist():
            itempostion = QPoint(position)
            if currenty > rect.height():
                currentx = itemwidths + OFFSET_X + 100
                currenty = itemmaxheight + 10

            itempostion.setX(currentx)
            itempostion.setY(currenty)

            _drawitem(icon, text, itempostion)
            currenty += OFFSET_Y

        position.setY(currenty + OFFSET_Y)


    def mousePressEvent(self, event):
        if self.framerect.contains(event.pos()):
            return

        self.api.events.showmap()
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

