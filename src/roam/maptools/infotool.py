from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QCursor, QPixmap

from qgis.gui import QgsMapToolIdentify


class InfoTool(QgsMapToolIdentify):
    """
        Inspection tool which copies the feature to a new layer
        and copies selected data from the underlying feature.
    """    
    infoResults = pyqtSignal(list)
    
    def __init__(self, canvas):
        QgsMapToolIdentify.__init__(self, canvas)
        self.canvas = canvas

    def canvasReleaseEvent(self, event):
        results = self.identify(event.x(), event.y(), QgsMapToolIdentify.TopDownAll)
        self.infoResults.emit(results)

    def isTransient(self):
        return True
