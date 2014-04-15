from PyQt4.QtCore import Qt, QSize, QRect, QPoint
from PyQt4.QtGui import  QWidget, QPixmap, QPainter, QLabel, QBrush, QColor

from qgis.core import QgsMapLayer

from roam.ui.uifiles import legend_widget


class LegendWidget(legend_widget, QWidget):
    def __init__(self, parent=None):
        super(LegendWidget, self).__init__(parent)
        self.setupUi(self)
        self.pixmap = None
        self.items = {}

        self.legendareabrush = QBrush(QColor(255,255,255,150))

    def paintEvent(self, event):
        def _drawitem(pixmap, text, postion):
            textpositon = QPoint(postion)
            textpositon.setX(pixmap.width() + 40)
            textpositon.setY(postion.y() + (pixmap.height() / 2))
            painter.drawPixmap(postion, pixmap)
            painter.drawText(textpositon, text)

        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.drawPixmap(event.rect(), self.pixmap)

        rect = event.rect()
        newrect = QRect(rect)
        newrect.setWidth(newrect.width() / 2)
        painter.setBrush(self.legendareabrush)
        painter.drawRect(newrect)

        titley = 50
        itemy = 40
        position = rect.topLeft() + QPoint(30, titley)
        for layer, items in self.items.iteritems():
            if len(items) == 1:
                itempostion = QPoint(position)
                itempostion.setY(itemy)
                _drawitem(items[0][1], layer, itempostion)
                itemy += 40
            else:
                for text, icon in items:
                    itempostion = QPoint(position)
                    itempostion.setY(itemy)
                    _drawitem(icon, text, itempostion)
                    itemy += 40

            position.setY(titley + itemy + 50)


    def updateitems(self, layers):
        self.items = {}
        for layer in layers:
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue

            items = layer.rendererV2().legendSymbologyItems(QSize(32, 32))
            self.items[layer.name()] = items

    def updatelegend(self, canvas):
        pixmap = QPixmap(canvas.size())
        pixmap.fill(canvas.canvasColor())
        painter = QPainter(pixmap)
        painter.setRenderHints(QPainter.Antialiasing)
        renderer = canvas.mapRenderer()
        renderer.render(painter)
        del painter
        self.pixmap = pixmap
        self.update()

