from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt4.QtGui import (QComboBox, QListView, QDialog, QGridLayout, QIcon, QFont, QTextBlockUserData,
                         QItemDelegate, QSortFilterProxyModel)

from qgis.core import QGis, QgsMapLayerRegistry, QgsMessageLog, QgsMapLayer

import os

import roam.editorwidgets

import configmanager.ui.resources_rc

plugin_path = os.path.dirname(os.path.realpath(__file__))

icons = {
    QGis.Point: ":/icons/PointLayer",
    QGis.Polygon: ":/icons/PolygonLayer",
    QGis.Line: ":/icons/LineLayer",
    QGis.NoGeometry: ":/icons/TableLayer"
}


class LayerFilter(QSortFilterProxyModel):
    """
    Filter a model to hide the given types of layers
    """
    def __init__(self, geomtypes=[QGis.NoGeometry], parent=None):
        super(LayerFilter, self).__init__(parent)
        self.geomtypes = geomtypes

    def filterAcceptsRow(self, sourcerow, soureparent):
        index = self.sourceModel().index(sourcerow, 0, soureparent)
        return not index.data(Qt.UserRole).geometryType() in self.geomtypes


class QgsLayerModel(QAbstractItemModel):
    def __init__(self, watchregistry=True, checkselect=False, parent=None):
        super(QgsLayerModel, self).__init__(parent)
        self.config = {}
        self.layerfilter = [QgsMapLayer.VectorLayer, QgsMapLayer.RasterLayer]
        self.layers = []
        self.checkselect = checkselect

        if watchregistry:
            QgsMapLayerRegistry.instance().layersAdded.connect(self.updateLayerList)
            QgsMapLayerRegistry.instance().layersRemoved.connect(self.updateLayerList)

    def findlayer(self, name):
        """
        Find a layer in the model by it's name
        """
        startindex = self.index(0, 0)
        items = self.match(startindex, Qt.DisplayRole, name)
        try:
            return items[0]
        except IndexError:
            return None

    def updateLayerList(self, *args):
        """
        Update the layer list. If no layers are given it will read from the map registry
        """
        self.beginResetModel()
        try:
            layers = args[0]
        except IndexError:
            layers = QgsMapLayerRegistry.instance().mapLayers().values()

        self.layers = []
        for layer in layers:
            if layer.type() in self.layerfilter:
                self.layers.append(layer)
        self.endResetModel()

    def flags(self, index):
        return Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def index(self, row, column, parent = QModelIndex()):
        layer = self.getLayer(row)
        if not layer: QModelIndex()
        return self.createIndex(row, column, layer)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self.layers)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def getLayer(self, index):
        try:
            layer = self.layers[index]
            if layer.type() in self.layerfilter:
                return layer
        except IndexError:
            return None

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
        elif role == Qt.CheckStateRole:
            if not self.checkselect:
                return
            try:
                if layer.name() in self.config['selectlayers']:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
            except KeyError:
                return Qt.Unchecked

    def configchanged(self):
        lastindex = self.index(self.rowCount(), self.rowCount())
        self.dataChanged.emit(self.index(0,0), lastindex)


class QgsFieldModel(QAbstractItemModel):
    FieldNameRole = Qt.UserRole + 1

    def __init__(self, layer=None, parent=None):
        super(QgsFieldModel, self).__init__(parent)
        self.config = {}
        if not layer is None:
            self.setLayer(layer)

        self.fields = []

    def setLayer(self, layer):
        self.layer = layer
        self.beginResetModel()
        self.fields = layer.pendingFields().toList()
        self.endResetModel()

    def findfield(self, name):
        """
        Find a field in the model by it's name
        """
        startindex = self.index(0,0)
        items = self.match(startindex, QgsFieldModel.FieldNameRole, name)
        try:
            return items[0]
        except IndexError:
            return None

    def updateLayer(self, index, index_before):
        if self.layermodel is None:
            return

        layer_index = self.layermodel.index(index.row(), index.column())
        layer = layer_index.internalPointer()
        self.setLayer(layer)

    def setLayerFilter(self, selectionModel):
        self.layermodel = selectionModel.model()
        selectionModel.currentChanged.connect(self.updateLayer)

    def index(self, row, column, parent = QModelIndex()):
        field = self.getField(row)
        if not field: QModelIndex()
        return self.createIndex(row, column, field)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent = QModelIndex()):
        return len(self.fields)

    def columnCount(self, parent = QModelIndex()):
        return 1

    def getField(self, index):
        try:
            return self.fields[index]
        except IndexError:
            return None

    def data(self, index, role):
        if not index.isValid(): return None
        if index.internalPointer() is None: return

        field = index.internalPointer()
        if role == Qt.DisplayRole:
            return "{} ({})".format(field.name(), field.typeName())
        elif role == Qt.UserRole:
            return field
        elif role == Qt.FontRole:
            try:
                if field.name() in self.config['layers'][self.layer.name()]['fields']:
                    font = QFont()
                    font.setBold(True)
                    return font
            except KeyError:
                return None
        elif role == QgsFieldModel.FieldNameRole:
            return field.name()

    def configchanged(self):
        lastindex = self.index(self.rowCount(), self.rowCount())
        self.dataChanged.emit(self.index(0,0), lastindex)


class WidgetsModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(WidgetsModel, self).__init__(parent)

    def findwidget(self, widgettype):
        """
        Find a field in the model by it's name
        """
        startindex = self.index(0, 0)
        items = self.match(startindex, Qt.DisplayRole, widgettype, -1)
        for item in items:
            if item.data(Qt.DisplayRole) == widgettype:
                return item
        return None

    def index(self, row, column, parent=QModelIndex()):
        widget = self.getWidget(row)
        if not widget: QModelIndex()
        return self.createIndex(row, column, widget)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(roam.editorwidgets.supportedwidgets)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def getWidget(self, index):
        try:
            return roam.editorwidgets.supportedwidgets[index]
        except IndexError:
            return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if not index.internalPointer():
            return None

        widgettype = index.internalPointer()
        if role == Qt.DisplayRole:
            return widgettype.widgettype
        elif role == Qt.UserRole:
            return widgetyype
        elif role == Qt.DecorationRole:
            return widgeticon(widgettype)


def widgeticon(widgettype):
    return QIcon(':/icons/{}'.format(widgettype))
