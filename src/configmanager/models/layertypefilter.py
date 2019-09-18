from PyQt5.QtCore import QSortFilterProxyModel, Qt
from qgis._core import QgsWkbTypes, QgsMapLayer


class LayerTypeFilter(QSortFilterProxyModel):
    """
    Filter a model to hide the given types of layers
    """

    def __init__(self, geomtypes=[QgsWkbTypes.NullGeometry], parent=None):
        super(LayerTypeFilter, self).__init__(parent)
        self.geomtypes = geomtypes
        self.setDynamicSortFilter(True)

    def filterAcceptsRow(self, sourcerow, soureparent):
        index = self.sourceModel().index(sourcerow, 0, soureparent)
        if not index.isValid():
            return False

        layer = index.data(Qt.UserRole)
        if not layer:
            return False

        if index.data(Qt.UserRole).type() == QgsMapLayer.RasterLayer:
            return False

        return not index.data(Qt.UserRole).geometryType() in self.geomtypes