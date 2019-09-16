from PyQt5.QtCore import QAbstractItemModel, Qt, QModelIndex


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
        self.fields = layer.fields().toList()
        self.endResetModel()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def findfield(self, name):
        """
        Find a field in the model by it's name
        """
        startindex = self.index(0, 0)
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

    def index(self, row, column, parent=QModelIndex()):
        field = self.getField(row)
        if not field: QModelIndex()
        return self.createIndex(row, column, field)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self.fields)

    def columnCount(self, parent=QModelIndex()):
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
        self.dataChanged.emit(self.index(0, 0), lastindex)