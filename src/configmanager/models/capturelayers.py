from PyQt5.QtCore import Qt

from configmanager.models import QgsLayerModel


class CaptureLayersModel(QgsLayerModel):
    def __init__(self, watchregistry=True, parent=None):
        super(CaptureLayersModel, self).__init__(watchregistry, parent)
        self.config = {}

    def setData(self, index, value, role=None):
        if role == Qt.CheckStateRole:
            selectlayers = self.config.get('selectlayers', [])
            self.config['selectlayers'] = selectlayers

            layer = index.internalPointer()
            layername = str(layer.name())

            if value == Qt.Checked:
                selectlayers.append(layername)
            else:
                selectlayers.remove(layername)
            self.dataChanged.emit(index, index)

        return super(CaptureLayersModel, self).setData(index, value, role)

    def data(self, index, role):
        if not index.isValid() or index.internalPointer() is None:
            return

        layer = index.internalPointer()
        if role == Qt.CheckStateRole:
            if layer.name() in self.config.get('selectlayers', {}):
                return Qt.Checked
            else:
                return Qt.Unchecked
        else:
            return super(CaptureLayersModel, self).data(index, role)