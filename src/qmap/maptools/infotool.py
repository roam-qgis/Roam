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
        results = self.identify(event.x(), event.y(), QgsMapToolIdentify.TopDownAll)
        self.infoResults.emit(results)
           
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
        return True

    def isEditTool(self):
        return False