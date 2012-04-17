from PointTool import PointTool, log
from PyQt4.QtGui import QAction, QIcon
from qgis.core import *
from qgis.gui import *
from forms.ListFeatureForm import ListFeaturesForm
import time
import resources
from DialogProvider import DialogProvider

class Timer():
   def __enter__(self): self.start = time.time()
   def __exit__(self, *args): log(str(time.time() - self.start))

class EditAction(QAction):
    def __init__(self, name, iface, layerstoformmapping ):
        QAction.__init__(self, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.layerstoformmapping = layerstoformmapping
        self.triggered.connect(self.setTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.findFeatures )
        self.setIcon(QIcon(":/icons/edit"))
        
    def setTool(self):
        self.canvas.setMapTool(self.tool)

    def findFeatures(self, point):
        self.searchRadius = self.canvas.extent().width() * ( 0.5 / 100.0)
        log("Finding Featues at %s with radius of %s" % (point, self.searchRadius))
        rect = QgsRectangle()
        rect.setXMinimum( point.x() - self.searchRadius );
        rect.setXMaximum( point.x() + self.searchRadius );
        rect.setYMinimum( point.y() - self.searchRadius );
        rect.setYMaximum( point.y() + self.searchRadius );
        
        featuresToForms = {}
        for layer in self.canvas.layers():
            if layer.type() == QgsMapLayer.RasterLayer:
                continue
                
            layer.select( layer.pendingAllAttributesList(), rect, True, True)
            name = layer.name()
            try:
                form = self.layerstoformmapping[str(name)]
                for feature in layer:
                    featuresToForms[feature] = (form, layer)
            except KeyError:
                continue

        if len(featuresToForms) == 1:
            form, layer = featuresToForms.itervalues().next()
            feature = featuresToForms.iterkeys().next()
            self.openForm(form, feature, layer)
        elif len(featuresToForms) > 0:
            listUi = ListFeaturesForm()
            listUi.loadFeatureList(featuresToForms)
            listUi.openFeatureForm.connect(self.openForm)
            listUi.exec_()
    
    def openForm(self,formmodule,feature,maplayer):
        if not maplayer.isEditable():
            maplayer.startEditing()

        self.dialogprovider = DialogProvider(self.canvas)
        self.dialogprovider.openDialog( formmodule, feature, maplayer, True )
        self.dialogprovider.accepted.connect(self.setTool)
        self.dialogprovider.rejected.connect(self.setTool)