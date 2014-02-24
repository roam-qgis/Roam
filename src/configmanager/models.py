from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt, pyqtSignal
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
        self.setDynamicSortFilter(True)

    def filterAcceptsRow(self, sourcerow, soureparent):
        index = self.sourceModel().index(sourcerow, 0, soureparent)
        if not index.isValid():
            return False

        if index.data(Qt.UserRole).type() == QgsMapLayer.RasterLayer:
            return False

        return not index.data(Qt.UserRole).geometryType() in self.geomtypes

class FormModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(FormModel, self).__init__(parent)
        self.forms = []

    def addform(self, form):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + 1)
        self.forms.append(form)
        self.endInsertRows()
        return self.index(self.rowCount() - 1, 0)

    def addforms(self, forms):
        self.beginResetModel()
        self.forms = forms
        self.endResetModel()

    def index(self, row, column, parnet=QModelIndex()):
        try:
            form = self.forms[row]
            return self.createIndex(row, column, form)
        except IndexError:
            return QModelIndex()

    def data(self, index, role):
        if not index.isValid() or index.internalPointer() is None:
            return

        form = index.internalPointer()
        if role == Qt.DisplayRole:
            return form.label
        if role == Qt.UserRole:
            return form
        if role == Qt.DecorationRole:
            return QIcon(form.icon)

    def rowCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self.forms)

    def columnCount(self, QModelIndex_parent=None, *args, **kwargs):
        return 1

    def parent(self, parent=None):
        return QModelIndex()

class QgsLayerModel(QAbstractItemModel):
    layerchecked = pyqtSignal(object, object, int)

    def __init__(self, watchregistry=True, checkselect=False, parent=None):
        super(QgsLayerModel, self).__init__(parent)
        self.config = {}
        self.layerfilter = [QgsMapLayer.VectorLayer, QgsMapLayer.RasterLayer]
        self.layers = []
        self.checkselect = checkselect

        if watchregistry:
            QgsMapLayerRegistry.instance().layerWasAdded.connect(self.addlayer)
            QgsMapLayerRegistry.instance().removeAll.connect(self.removeall)

    def findlayer(self, name):
        """
        Find a layer in the model by it's name
        """
        startindex = self.index(0, 0)
        items = self.match(startindex, Qt.DisplayRole, name)
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
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            self.addlayer(layer)

    def flags(self, index):
        return Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def index(self, row, column, parent = QModelIndex()):
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

    def setData(self, index, value, role=None):
        if role == Qt.CheckStateRole:
            self.layerchecked.emit(index, index.data(Qt.UserRole), value)

        return super(QgsLayerModel, self).setData(index, value, role)

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

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

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
        if not index.isValid():
            return None
        if index.internalPointer() is None:
            return

        field = index.internalPointer()
        if role == Qt.DisplayRole:
            return "{} ({})".format(field.name(), field.typeName())
        elif role == Qt.UserRole:
            return field
        elif role == QgsFieldModel.FieldNameRole:
            return field.name().lower()

    def configchanged(self):
        lastindex = self.index(self.rowCount(), self.rowCount())
        self.dataChanged.emit(self.index(0,0), lastindex)


class WidgetsModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(WidgetsModel, self).__init__(parent)
        self.widgets = []

    def addwidget(self, widget):
        count = self.rowCount()
        self.beginInsertRows(QModelIndex(), count, count + 1)
        self.widgets.append(widget)
        self.endInsertRows()
        return self.index(self.rowCount() - 1, 0)

    def loadwidgets(self, widgets):
        self.beginResetModel()
        self.widgets = widgets
        self.endResetModel()

    def index(self, row, column, parent=QModelIndex()):
        widget = self.getWidget(row)
        if not widget:
            return QModelIndex()
        return self.createIndex(row, column, widget)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self.widgets)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def getWidget(self, index):
        try:
            return self.widgets[index]
        except IndexError:
            return None

    def removeRow(self, row, parent=None):
        self.beginRemoveRows(QModelIndex(), row, row)
        del self.widgets[row]
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=None):
        if role == Qt.UserRole and index.isValid():
            widget = self.data(index, Qt.UserRole)
            widget.update(value)
            self.dataChanged.emit(index, index)
            return True

        return False

    def data(self, index, role):
        if not index.isValid():
            return None
        if not index.internalPointer():
            return None

        widget = index.internalPointer()
        if role == Qt.DisplayRole:
            field = widget.get('field', '') or ''
            return "{} ({})".format(widget['widget'], field.lower())
        elif role == Qt.UserRole:
            return widget
        elif role == Qt.DecorationRole:
            return widgeticon(widget['widget'])


def widgeticon(widgettype):
    return QIcon(':/icons/{}'.format(widgettype))
