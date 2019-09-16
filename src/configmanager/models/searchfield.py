from PyQt5.QtCore import Qt

from configmanager.models import QgsFieldModel


class SearchFieldsModel(QgsFieldModel):
    def __init__(self, parent=None):
        super(SearchFieldsModel, self).__init__(parent)
        self.config = {}

    def setData(self, index, value, role=None):
        if role == Qt.CheckStateRole:
            field = index.internalPointer()
            fieldname = str(field.name())

            if value == Qt.Checked:
                self.layerconfig.append(fieldname)
            else:
                self.layerconfig.remove(fieldname)
            self.dataChanged.emit(index, index)

        return super(SearchFieldsModel, self).setData(index, value, role)

    def flags(self, index):
        return Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def set_settings(self, config):
        self.config = config
        config = self.config.get("search", {})
        self.layerconfig = config.get(self.layer.name(), {}).get("columns", [])

        lastindex = self.index(self.rowCount(), self.rowCount())
        self.dataChanged.emit(self.index(0, 0), lastindex)

    def data(self, index, role):
        if not index.isValid() or index.internalPointer() is None:
            return

        field = index.internalPointer()
        if role == Qt.CheckStateRole:
            if field.name() in self.layerconfig:
                return Qt.Checked
            else:
                return Qt.Unchecked
        else:
            return super(SearchFieldsModel, self).data(index, role)