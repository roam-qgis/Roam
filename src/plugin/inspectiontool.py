from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QCursor, QPixmap
from qgis.core import (QgsPoint, QgsRectangle, QgsTolerance, 
                       QgsFeatureRequest, QgsFeature, QgsGeometry)
from qgis.gui import QgsMapTool

class InspectionTool(QgsMapTool):
    """
        Inspection tool which copies the feature to a new layer
        and copies selected data from the underlying feature.
    """
    
    finished = pyqtSignal(QgsFeature)
    
    def __init__(self, canvas, layerfrom, layerto, fieldsToCopy):
        """
            fieldsToCopy - A dict of field - field mapping with values to
                            copy to the new layer
        """
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.layerfrom = layerfrom
        self.layerto = layerto
        self.fields = fieldsToCopy
        self.searchRadius = QgsTolerance.toleranceInMapUnits( 10, layerfrom, \
                                                         self.canvas.mapRenderer(), QgsTolerance.Pixels)

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




    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

        rect = QgsRectangle()                                                 
        rect.setXMinimum(point.x() - self.searchRadius)
        rect.setXMaximum(point.x() + self.searchRadius)
        rect.setYMinimum(point.y() - self.searchRadius)
        rect.setYMaximum(point.y() + self.searchRadius)
        
        rq = QgsFeatureRequest().setFilterRect(rect)
        
        # Look for an existing feature first. If there is one
        # then we emit that back to qmap.
        try:
            feature = self.layerto.GetFeatures(rq).next()
            self.finished.emit(feature)
            return
        except StopIteration:
            pass
        
        
        try:
            # Only supports the first feature
            # TODO build picker to select which feature to inspect
            feature = self.layerfrom.GetFeatures(rq).next()
            newfeature = QgsFeature(self.layerto.pendingFields())
            newfeature.setGeometry(QgsGeometry(feature.geometry()))
            for fieldfrom, fieldto in self.fields.iteritems():
                # Assign the old values to the new feature
                newfeature[fieldto] = feature[fieldfrom]
                
            self.finished.emit(newfeature)
            return
        except StopIteration:
            return
        

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

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
