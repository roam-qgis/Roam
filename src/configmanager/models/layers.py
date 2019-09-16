from PyQt5.QtCore import QAbstractItemModel, pyqtSignal, Qt, QModelIndex
from PyQt5.QtGui import QIcon
from qgis._core import QgsMapLayer, QgsProject

from configmanager.icons import icons


class QgsLayerModel(QAbstractItemModel):
    layerchecked = pyqtSignal(object, object, int)

    def __init__(self, watchregistry=True, parent=None):
        super(QgsLayerModel, self).__init__(parent)
        self.layerfilter = [QgsMapLayer.VectorLayer, QgsMapLayer.RasterLayer]
        self.layers = []

        if watchregistry:
            QgsProject.instance().layerWasAdded.connect(self.addlayer)
            QgsProject.instance().removeAll.connect(self.removeall)

    def findlayer(self, name):
        """
        Find a layer in the model by it's name
        """
        startindex = self.index(0, 0)
        items = self.match(startindex, Qt.DisplayRole, name, 1, Qt.MatchExactly | Qt.MatchWrap)
        try:
            return items[0]
        except IndexError:
            return QModelIndex()

    def addlayer(self, layer):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + 1)
        try:
            if layer.type() in self.layerfilter:
                self.layers.append(layer)
        except AttributeError:
            pass
        self.endInsertRows()

    def removeall(self):
        self.beginResetModel()
        self.layers = []
        self.endResetModel()

    def addlayers(self, layers, removeall=False):
        if removeall:
            self.removeall()

        for layer in layers:
            self.addlayer(layer)

    def refresh(self):
        self.removeall()
        for layer in QgsProject.instance().mapLayers().values():
            self.addlayer(layer)

    def flags(self, index):
        return Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def index(self, row, column, parent=QModelIndex()):
        def getLayer(index):
            try:
                layer = self.layers[index]
                if layer.type() in self.layerfilter:
                    return layer
            except IndexError:
                return None

        layer = getLayer(row)
        if not layer:
            return QModelIndex()

        return self.createIndex(row, column, layer)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self.layers)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role):
        if not index.isValid() or index.internalPointer() is None:
            return

        layer = index.internalPointer()
        if role == Qt.DisplayRole:
            return layer.name()
        elif role == Qt.DecorationRole:
            if layer.type() == QgsMapLayer.RasterLayer:
                return

            geomtype = layer.geometryType()
            return QIcon(icons.get(geomtype, None))
        elif role == Qt.UserRole:
            return layer