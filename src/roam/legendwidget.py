import math
import functools
from qgis.PyQt.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QRectF
from qgis.PyQt.QtWidgets import QWidget, QLabel
from qgis.PyQt.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QTextOption, QFontMetrics, QImage, QFont

from qgis.core import QgsLayerTreeModel, QgsLayerTreeNode
from qgis.core import QgsMapRendererParallelJob

from ui.ui_legend import Ui_legendsWidget

ICON_SIZE = QSize(32, 32)


class LegendWidget(Ui_legendsWidget, QWidget):
    showmap = pyqtSignal()

    def __init__(self, parent=None):
        super(LegendWidget, self).__init__(parent)
        self.setupUi(self)

        self.previewImage.mousePressEvent = self.previewImagePressEvent
        self.previewImage.resizeEvent = self.update
        self.btnExpand.pressed.connect(self.layerTree.expandAllNodes)
        self.btnCollapse.pressed.connect(self.layerTree.collapseAllNodes)
        self.canvas = None

    def init(self, canvas):
        self.canvas = canvas
        self.canvas.extentsChanged.connect(self.update_legend_map_data)

    def update_legend_map_data(self):
        if not self.layerTree.layerTreeModel():
            return
        self.layerTree.layerTreeModel().setLegendMapViewData(
            self.canvas.mapUnitsPerPixel(), self.canvas.mapSettings().outputDpi(), self.canvas.scale())

    def previewImagePressEvent(self, event):
        self.showmap.emit()

    def showEvent(self, showevent):
        self.canvas.renderStarting.connect(self.update)
        self.update()

    def hideEvent(self, hideevent):
        self.canvas.renderStarting.disconnect(self.update)

    def setRoot(self, root):
        model = QgsLayerTreeModel(root, self)
        model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility)
        model.setFlag(QgsLayerTreeModel.ShowLegendAsTree)
        font = QFont()
        font.setPointSize(20)
        model.setLayerTreeNodeFont(QgsLayerTreeNode.NodeLayer, font)
        model.setLayerTreeNodeFont(QgsLayerTreeNode.NodeGroup, font)
        self.layerTree.setModel(model)

    def _renderimage(self):
        image = self.renderjob.renderedImage()
        self.previewImage.setPixmap(QPixmap.fromImage(image))

    def update(self, *__args):
        settings = self.canvas.mapSettings()
        settings.setOutputSize(self.previewImage.size())
        self.renderjob = QgsMapRendererParallelJob(settings)
        self.renderjob.finished.connect(self._renderimage)
        self.renderjob.start()
