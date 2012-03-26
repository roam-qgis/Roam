from PointTool import PointTool, log
from PyQt4.QtGui import QAction
from PyQt4.QtCore import QSettings
from qgis.core import *
from qgis.gui import *
from forms.ListFeatureForm import ListFeaturesForm

class EditAction(QAction):
    def __init__(self, name, iface, layerstoformmapping ):
        QAction.__init__(self, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.layerstoformmapping = layerstoformmapping
        self.triggered.connect(self.runPointTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.findFeatures )
        self.searchRadius = self.canvas.extent().width() * ( 0.5 / 100.0)
        
    def runPointTool(self):
        self.canvas.setMapTool(self.tool)

    def findFeatures(self, point):
        log("Finding Featues at %s with radius of %s" % (point, self.searchRadius))
        
        rect = QgsRectangle()
        rect.setXMinimum( point.x() - self.searchRadius );
        rect.setXMaximum( point.x() + self.searchRadius );
        rect.setYMinimum( point.y() - self.searchRadius );
        rect.setYMaximum( point.y() + self.searchRadius );
        
        featuresToForms = {}
        for layer in self.canvas.layers():
            layer.select( layer.pendingAllAttributesList(), rect, True, True)
            name = layer.name()
            form = self.layerstoformmapping.get(str(name),"Default")
            for feature in layer:
                featuresToForms[feature] = form

        listUi = ListFeaturesForm()
        listUi.loadFeatueList(featuresToForms)
        listUi.exec_()