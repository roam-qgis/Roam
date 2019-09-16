from PyQt5.QtCore import QSortFilterProxyModel, Qt


class CaptureLayerFilter(QSortFilterProxyModel):
    """
    Filter a layer model to only show select layers.
    """

    def __init__(self, parent=None):
        super(CaptureLayerFilter, self).__init__(parent)
        self.selectlayers = []
        self.setDynamicSortFilter(True)

    def setSelectLayers(self, layers):
        self.selectlayers = layers
        self.invalidateFilter()

    def filterAcceptsRow(self, sourcerow, soureparent):
        index = self.sourceModel().index(sourcerow, 0, soureparent)
        if not index.isValid():
            return False

        layer = index.data(Qt.UserRole)
        if layer.name() in self.selectlayers:
            return True

        return False