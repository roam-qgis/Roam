from PyQt4.QtCore import Qt, QSize
from PyQt4.QtGui import  QWidget, QPixmap, QPainter, QLabel

from qgis.core import QgsMapLayer

from roam.ui.uifiles import legend_widget


class LegendWidget(legend_widget, QWidget):
    def __init__(self, parent=None):
        super(LegendWidget, self).__init__(parent)
        self.setupUi(self)

    def updateitems(self, layers):
        layout = self.legendItems.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

        for layer in layers:
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue

            items = layer.rendererV2().legendSymbologyItems(QSize(32, 32))
            for name, icon in items:
                iconlabel = QLabel()
                iconlabel.setPixmap(icon)
                namelabel = QLabel(name)
                self.legendItems.layout().addRow(iconlabel, namelabel)

    def updatelegend(self, canvas):
        pixmap = QPixmap(canvas.size())
        pixmap.fill(canvas.canvasColor())
        painter = QPainter(pixmap)
        renderer = canvas.mapRenderer()
        renderer.render(painter)
        del painter
        h = self.snapshotLabel.height()
        pixmap = pixmap.scaledToHeight(h, Qt.SmoothTransformation)
        self.snapshotLabel.setPixmap(pixmap)

