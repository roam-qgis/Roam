from FormBinder import FormBinder
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

log = lambda msg: QgsMessageLog.logMessage(msg ,"SDRC")

# Vertex Finder Tool class
class PointTool(QgsMapTool):
    mouseClicked = pyqtSignal(QgsPoint)

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.m1 = None
        self.p1 = QgsPoint()
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

    def setAsMapTool(self):
        self.canvas.setMapTool(self)

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.p1.setX(point.x())
        self.p1.setY(point.y())

        self.mouseClicked.emit(self.p1)
        

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        self.canvas.scene().removeItem(self.m1)
        self.m1 = None
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True


class PointAction(QAction):
    def __init__(self, name, iface, form ):
        QAction.__init__(self, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.form = form
        self.triggered.connect(self.runPointTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.pointClick )
        self.layer = None

        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            if layer.name() == self.form.__layerName__:
                self.layer = layer

        if self.layer is None:
            self.setEnabled(False)
            self.setToolTip("Can't find the layer for the tool")
            
    def runPointTool(self):
        self.canvas.setMapTool(self.tool)

    def pointClick(self, point):
        self.layer.startEditing()
        fields = self.layer.pendingFields()
        provider = self.layer.dataProvider()
        dialoginstance = self.form.dialogInstance()
        
        binder = FormBinder(self.layer, dialoginstance)

        feature = QgsFeature()
        feature.setGeometry( QgsGeometry.fromPoint( point ) )


        for id in fields.keys():
            feature.addAttribute( id, provider.defaultValue( id ) )

        binder.bindFeature(feature)

        if dialoginstance.exec_():
            log("Saving values back")
            feature = binder.unbindFeature(feature)
            log("New feature %s" % feature)
            for value in feature.attributeMap().values():
                log("New value %s" % value.toString())
                
            self.layer.addFeature( feature )
            self.canvas.refresh()
            self.layer.commitChanges()
            
        