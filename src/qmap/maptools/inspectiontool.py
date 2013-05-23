from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QCursor, QPixmap
from qgis.core import (QgsPoint, QgsRectangle, QgsTolerance, 
                       QgsFeatureRequest, QgsFeature, QgsGeometry,
                       QgsVectorLayer)
from qgis.gui import QgsMapTool

class InspectionTool(QgsMapTool):
    """
        Inspection tool which copies the feature to a new layer
        and copies selected data from the underlying feature.
    """
    
    finished = pyqtSignal(QgsVectorLayer, QgsFeature)
    
    def __init__(self, canvas, layerfrom, layerto, mapping):
        """
            mapping - A dict of field - field mapping with values to
                            copy to the new layer
        """
        QgsMapTool.__init__(self, canvas)
        self.layerfrom = layerfrom
        self.layerto = layerto
        self.fields = mapping
        self.searchRadius = (QgsTolerance.toleranceInMapUnits( 10, layerfrom,
                                                               self.canvas().mapRenderer(), QgsTolerance.Pixels))

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

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())

        rect = QgsRectangle()                                                 
        rect.setXMinimum(point.x() - self.searchRadius)
        rect.setXMaximum(point.x() + self.searchRadius)
        rect.setYMinimum(point.y() - self.searchRadius)
        rect.setYMaximum(point.y() + self.searchRadius)
        
        rq = QgsFeatureRequest().setFilterRect(rect)
        
        # Look for an existing feature first. If there is one
        # then we emit that back to qmap.
        try:
            feature = self.layerto.getFeatures(rq).next()
            self.finished.emit(self.layerto, feature)
            return
        except StopIteration:
            pass
        
        
        try:
            # Only supports the first feature
            # TODO build picker to select which feature to inspect
            feature = self.layerfrom.getFeatures(rq).next()
            fields = self.layerto.pendingFields()
            newfeature = QgsFeature(fields)
            newfeature.setGeometry(QgsGeometry(feature.geometry()))
            
            #Set the default values
            for indx in xrange(fields.count()):
                newfeature[indx] = self.layerto.dataProvider().defaultValue( indx )
            
            # Assign the old values to the new feature
            for fieldfrom, fieldto in self.fields.iteritems():      
                newfeature[fieldto] = feature[fieldfrom]
                
            self.finished.emit(self.layerto, newfeature)
        except StopIteration:
            pass
        

    def activate(self):
        """
        Set the tool as the active tool in the canvas. 

        @note: Should be moved out into qmap.py 
               and just expose a cursor to be used
        """
        self.canvas().setCursor(self.cursor)

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
