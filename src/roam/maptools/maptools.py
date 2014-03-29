from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from roam.maptools.touchtool import TouchMapTool

import roam.resources_rc

class RubberBand(QgsRubberBand):
    def __init__(self, canvas, geometrytype, width=5, iconsize=20):
        super(RubberBand, self).__init__(canvas, geometrytype)
        self.canvas = canvas
        self.setIconSize(iconsize)
        self.setWidth(width)
        self.iconsize = iconsize
        self.textpen = QPen(Qt.black)
        self.textpen.setWidth(2)
        self.distancearea = QgsDistanceArea()
        self.createdistancearea()
        self.unit = self.canvas.mapRenderer().destinationCrs().mapUnits()

    def createdistancearea(self):
        self.distancearea.setSourceCrs( self.canvas.mapRenderer().destinationCrs().srsid())
        ellispoid = QgsProject.instance().readEntry("Measure", "/Ellipsoid", GEO_NONE)
        self.distancearea.setEllipsoid(ellispoid[0])
        ellispoidemode = self.canvas.mapRenderer().hasCrsTransformEnabled()
        self.distancearea.setEllipsoidalMode(ellispoidemode)

    def paint(self, p, option, widget):
        super(RubberBand, self).paint(p)

        offset = QPointF(self.iconsize + 25, 0)
        nodescount = self.numberOfVertices()
        for index in xrange(nodescount, -1, -1):
            if index == 0:
                return

            qgspoint = self.getPoint(0, index)
            qgspointbefore = self.getPoint(0, index - 1)
            # No point before means we are the first index and there is nothing
            # before us.
            if not qgspointbefore:
                return

            if qgspoint and qgspointbefore:
                distance = self.distancearea.measureLine( qgspoint, qgspointbefore)
                point = self.toCanvasCoordinates(qgspoint) - self.pos()
                point += offset
                p.setPen(self.textpen)
                text = QgsDistanceArea.textUnit(distance, 3, self.unit, False)
                p.drawText(point, text)

    def boundingRect(self):
        rect = super(RubberBand, self).boundingRect()
        width = rect.size().width()
        rect.setWidth(width + 200)
        return rect


class EndCaptureAction(QAction):
    def __init__(self, tool, parent=None):
        super(EndCaptureAction, self).__init__(QIcon(":/icons/stop-capture"), QApplication.translate("EndCaptureAction", "End Capture", None, QApplication.UnicodeUTF8), parent)
        self.setObjectName("endcapture")
        self.setCheckable(False)
        self.tool = tool
        self.isdefault = False
        self.ismaptool = False


class CaptureAction(QAction):
    def __init__(self, tool, geomtype, parent=None):
        super(CaptureAction, self).__init__(QIcon(":/icons/capture-{}".format(geomtype)), QApplication.translate("CaptureAction", "Capture", None, QApplication.UnicodeUTF8), parent)
        self.setObjectName("capture")
        self.setCheckable(True)
        self.tool = tool
        self.isdefault = True
        self.ismaptool = True


class PolylineTool(QgsMapTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(PolylineTool, self).__init__(canvas)
        self.points = []
        self.canvas = canvas
        self.band = RubberBand(self.canvas, QGis.Line, width=5, iconsize=20)
        self.band.setColor(QColor.fromRgb(224,162,16, 75))
        self.pointband = QgsRubberBand(self.canvas, QGis.Point)
        self.pointband.setColor(QColor.fromRgb(224,162,16, 100))
        self.pointband.setIconSize(20)
        self.snapper = QgsMapCanvasSnapper(self.canvas)
        self.capturing = False
        self.cursor = QCursor(QPixmap(["16 16 3 1",
            "      c None",
            ".     c #FF0000",
            "+     c #FFFFFF",
            "                ",
            "       +.+      ",
            "      ++.++     ",
            "     +.....+    ",
            "    +.     .+   ",
            "   +.   .   .+  ",
            "  +.    .    .+ ",
            " ++.    .    .++",
            " ... ...+... ...",
            " ++.    .    .++",
            "  +.    .    .+ ",
            "   +.   .   .+  ",
            "   ++.     .+   ",
            "    ++.....+    ",
            "      ++.++     ",
            "       +.+      "]))

        self.captureaction = CaptureAction(self, "line")
        self.endcaptureaction = EndCaptureAction(self)

        self.captureaction.toggled.connect(self.endcaptureaction.setEnabled)
        self.endcaptureaction.setEnabled(False)

        self.endcaptureaction.triggered.connect(self.endcapture)

    @property
    def actions(self):
        return [self.captureaction, self.endcaptureaction]

    def canvasPressEvent(self, event):
        # TODO Add node dragging support.
        pass

    def getPointFromEvent(self, event):
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        return point

    def canvasMoveEvent(self, event):
        if self.capturing:
            point = self.snappoint(event.pos())
            self.band.movePoint(point)
        
    def canvasReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.endcapture()
        else:
            point = self.snappoint(event.pos())
            qgspoint = QgsPoint(point)
            self.points.append(qgspoint)
            self.band.addPoint(point)
            self.pointband.addPoint(point)
            self.capturing = True
            self.endcaptureaction.setEnabled(True)

    def endcapture(self):
        self.capturing = False
        self.band.removeLastPoint()
        geometry = self.band.asGeometry()
        if not geometry:
            return

        self.geometryComplete.emit(geometry)

    def clearBand(self):
        self.reset()

    def reset(self):
        self.band.reset(QGis.Line)
        self.pointband.reset(QGis.Point)
        self.points = []

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        self.reset()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def snappoint(self, point):
        try:
            _, results = self.snapper.snapToBackgroundLayers(point)
            point = results[0].snappedVertex
            return point
        except IndexError:
            return self.canvas.getCoordinateTransform().toMapCoordinates(point)


class PolygonTool(PolylineTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(PolygonTool, self).__init__(canvas)
        self.captureaction = CaptureAction(self, "polygon")
        self.reset()

    def reset(self):
        super(PolygonTool, self).reset()
        self.band.reset(QGis.Polygon)


class PointTool(TouchMapTool):
    """
    A basic point tool that can be connected to actions in order to handle
    point based actions.
    """
    geometryComplete = pyqtSignal(QgsGeometry)
    
    def __init__(self, canvas):
        super(PointTool, self).__init__(canvas)
        self.cursor = QCursor(QPixmap(["16 16 3 1",
            "      c None",
            ".     c #FF0000",
            "+     c #FFFFFF",
            "                ",
            "       +.+      ",
            "      ++.++     ",
            "     +.....+    ",
            "    +.     .+   ",
            "   +.   .   .+  ",
            "  +.    .    .+ ",
            " ++.    .    .++",
            " ... ...+... ...",
            " ++.    .    .++",
            "  +.    .    .+ ",
            "   +.   .   .+  ",
            "   ++.     .+   ",
            "    ++.....+    ",
            "      ++.++     ",
            "       +.+      "]))

        self.captureaction = CaptureAction(self, 'point')

    @property
    def actions(self):
        return [self.captureaction]

    def canvasReleaseEvent(self, event):
        if self.pinching:
            return

        if self.dragging:
            super(PointTool, self).canvasReleaseEvent(event)
            return

        point = self.toMapCoordinates(event.pos())
        self.geometryComplete.emit(QgsGeometry.fromPoint(point))
        
    def activate(self):
        """
        Set the tool as the active tool in the canvas. 

        @note: Should be moved out into qmap.py 
               and just expose a cursor to be used
        """
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        pass

    def clearBand(self):
        self.band.reset()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False
