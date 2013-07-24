from PyQt4.QtCore import pyqtSignal
from qgis.gui import QgsMapTool

class MapTool(QgsMapTool):
    """
        Base map tool.
    """
    layersupdated = pyqtSignal(bool)
    def __init__(self, canvas, layers):
        QgsMapTool.__init__(self, canvas)
        self._layers = layers
    
    @property
    def layers(self):
        return self._layers
        
    @layers.setter
    def layers(self, layers):
        self._layers = layers
        self.layersupdated.emit(False)
        
    def addLayer(self, layer):
        self.layers.append(layer)
        self.layersupdated.emit(True)
