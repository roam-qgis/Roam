from point_tool import PointTool, log
from PyQt4.QtGui import QAction, QIcon
from qgis.core import *
from qgis.gui import *
from forms.ListFeatureForm import ListFeaturesForm
import resources_rc
from dialog_provider import DialogProvider

class EditAction(QAction):
    def __init__(self, name, iface ):
        QAction.__init__(self, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.layerstoformmapping = {}
        self.triggered.connect(self.setTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.findFeatures )
        self.setIcon(QIcon(":/icons/edit"))
        self.dialogprovider = DialogProvider(self.canvas, iface)
        self.dialogprovider.accepted.connect(self.setTool)
        self.dialogprovider.rejected.connect(self.setTool)
        self.setCheckable(True)
        
    def setTool(self):
        self.canvas.setMapTool(self.tool)

    def findFeatures(self, point):
        #If we don't have a any layers to forms mappings yet just exit.
        if not self.layerstoformmapping:
            return

        layer = self.layerstoformmapping.iterkeys().next()

        searchRadius = QgsTolerance.toleranceInMapUnits( 5, layer, \
                                                         self.canvas.mapRenderer(), QgsTolerance.Pixels)

        rect = QgsRectangle()                                                 
        rect.setXMinimum( point.x() - searchRadius );
        rect.setXMaximum( point.x() + searchRadius );
        rect.setYMinimum( point.y() - searchRadius );
        rect.setYMaximum( point.y() + searchRadius );

        log("Finding Featues at %s with radius of %s" % (point, searchRadius))
        
        featuresToForms = {}
        for layer, form in self.layerstoformmapping.iteritems():
            layer.select( layer.pendingAllAttributesList(), rect, True, True)
            for feature in layer:
                featuresToForms[feature] = (form, layer)

        if len(featuresToForms) == 1:
            form, layer = featuresToForms.itervalues().next()
            feature = featuresToForms.iterkeys().next()
            self.openForm(form, feature, layer)
        elif len(featuresToForms) > 0:
            listUi = ListFeaturesForm()
            listUi.loadFeatureList(featuresToForms)
            listUi.openFeatureForm.connect(self.openForm)
            listUi.exec_()

    def setLayersForms(self,layerforms):
        self.layerstoformmapping = layerforms
    
    def openForm(self,formmodule,feature,maplayer):
        if not maplayer.isEditable():
            maplayer.startEditing()

        self.dialogprovider.openDialog( formmodule, feature, maplayer, True )
            