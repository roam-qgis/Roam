from PyQt5.QtCore import pyqtSignal
from qgis._core import QgsPoint, QgsGeometry, QgsWkbTypes

from roam.maptools.polylinetool import PolylineTool
from roam.maptools.actions import CaptureAction


class PolygonTool(PolylineTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)
    MODE = "POLYGON"

    def __init__(self, canvas, config=None):
        super(PolygonTool, self).__init__(canvas, config)
        self.minpoints = 3
        self.captureaction = CaptureAction(self, "polygon", text="Digitize")
        self.captureaction.toggled.connect(self.update_state)
        self.reset()

    def reset(self):
        super(PolygonTool, self).reset()
        self.band.reset(QgsWkbTypes.PolygonGeometry)