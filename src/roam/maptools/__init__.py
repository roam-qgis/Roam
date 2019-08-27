from qgis.core import QgsWkbTypes

from roam.maptools.maptools import PointTool, PolygonTool, PolylineTool
from roam.maptools.inspectiontool import InspectionTool
from roam.maptools.movetool import MoveTool
from roam.maptools.edittool import EditTool
from roam.maptools.infotool import InfoTool
from roam.maptools.touchtool import TouchMapTool

tools = {QgsWkbTypes.PointGeometry: PointTool,
         QgsWkbTypes.PolygonGeometry: PolygonTool,
         QgsWkbTypes.LineGeometry: PolylineTool}

