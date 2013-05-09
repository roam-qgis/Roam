from maptools import PointTool
from PyQt4.QtGui import QAction, QIcon, QColor
from PyQt4.QtCore import Qt
from qgis.core import *
from qgis.gui import *
from listfeatureform import ListFeaturesForm
import resources_rc
from dialog_provider import DialogProvider
import qmap

class EditAction(QAction):
    def __init__(self, name, iface ):
        QAction.__init__(self, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.toggled.connect(self.setTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.findFeatures )
        self.tool.mouseMove.connect(self.highlightFeatures)
        
        self.setIcon(QIcon(":/icons/edit"))
        self.dialogprovider = DialogProvider(self.canvas, iface)
        self.dialogprovider.accepted.connect(self.setTool)
        self.dialogprovider.rejected.connect(self.setTool)
        self.setCheckable(True)
        self.band = QgsRubberBand(self.canvas)
        self.band.setColor(QColor.fromRgb(224,162,16))
        self.band.setWidth(3)

    def setTool(self):
        self.canvas.setMapTool(self.tool)

    def findFeatures(self, point):
        #If we don't have a any layers to forms mappings yet just exit.
        if not qmap.QMap.layerformmap:
            return

        layer = qmap.QMap.layerformmap[0]

        searchRadius = QgsTolerance.toleranceInMapUnits( 10, layer, \
                                                         self.canvas.mapRenderer(), QgsTolerance.Pixels)

        rect = QgsRectangle()                                                 
        rect.setXMinimum( point.x() - searchRadius );
        rect.setXMaximum( point.x() + searchRadius );
        rect.setYMinimum( point.y() - searchRadius );
        rect.setYMaximum( point.y() + searchRadius );
                
        featuresToForms = []
        for layer in qmap.QMap.layerformmap:
            rq = QgsFeatureRequest().setFilterRect(rect)
            for feature in layer.getFeatures(rq):
                featuresToForms.append((feature, layer))

        if len(featuresToForms) == 1:
            layer = featuresToForms[0][1]
            feature = featuresToForms[0][0]
            self.openForm(feature, layer)
        elif len(featuresToForms) > 0:
            listUi = ListFeaturesForm()
            listUi.loadFeatureList(featuresToForms)
            listUi.openFeatureForm.connect(self.openForm)
            listUi.exec_()
        
    def highlightFeatures(self, point):
        if not qmap.QMap.layerformmap:
            return

        layer = qmap.QMap.layerformmap[0]

        searchRadius = QgsTolerance.toleranceInMapUnits( 5, layer, \
                                                         self.canvas.mapRenderer(), QgsTolerance.Pixels)
        rect = QgsRectangle()
        rect.setXMinimum( point.x() - searchRadius );
        rect.setXMaximum( point.x() + searchRadius );
        rect.setYMinimum( point.y() - searchRadius );
        rect.setYMaximum( point.y() + searchRadius );

        self.band.reset()
        for layer in qmap.QMap.layerformmap:
            rq = QgsFeatureRequest().setFilterRect(rect) 
            for feature in layer.getFeatures(rq):
                if not feature.isValid():
                    continue
                self.band.addGeometry(feature.geometry(), None)

    def setLayersForms(self,layerforms):
        qmap.QMap.layerformmap = layerforms
    
    def openForm(self, feature, maplayer):
        if not maplayer.isEditable():
            maplayer.startEditing()

        self.dialogprovider.openDialog( feature, maplayer, True )

    def deactivate(self):
        self.band.hide()