from PointTool import PointTool, log
from PyQt4.QtGui import QAction
from qgis.core import *
from qgis.gui import *
from forms.ListFeatureForm import ListFeaturesForm
from FormBinder import FormBinder
import time

class Timer():
   def __enter__(self): self.start = time.time()
   def __exit__(self, *args): log(str(time.time() - self.start))

class EditAction(QAction):
    def __init__(self, name, iface, layerstoformmapping ):
        QAction.__init__(self, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.layerstoformmapping = layerstoformmapping
        self.triggered.connect(self.runPointTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.findFeatures )
        
        
    def runPointTool(self):
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
            layer.select( layer.pendingAllAttributesList(), rect, True, True)
            name = layer.name()
            form = self.layerstoformmapping.get(str(name),"Default")
            for feature in layer:
                featuresToForms[feature] = (form, layer)

        if len(featuresToForms) > 0:
            listUi = ListFeaturesForm()
            listUi.loadFeatureList(featuresToForms)
            listUi.openFeatureForm.connect(self.openForm)
            listUi.exec_()
    
    def openForm(self,form,feature,maplayer):
        with Timer():
            if not maplayer.isEditable():
                maplayer.startEditing()

            dialog = form.dialogInstance()
            binder = FormBinder(maplayer, dialog)
            binder.bindFeature(feature)
            if dialog.exec_():
                log("Saving values back")
                feature = binder.unbindFeature(feature)
                log("New feature %s" % feature)
                for value in feature.attributeMap().values():
                    log("New value %s" % value.toString())

                maplayer.updateFeature( feature )
                maplayer.commitChanges()
                self.canvas.refresh()