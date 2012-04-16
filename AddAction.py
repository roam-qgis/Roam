from PointTool import PointTool, log
from PyQt4.QtGui import QAction
from PyQt4.QtCore import QSettings
from qgis.core import *
from qgis.gui import *
import uuid
from forms.ListFeatureForm import ListFeaturesForm
from FormBinder import FormBinder
import time
import os
class AddAction(QAction):
    def __init__(self, name, iface, form, layer ):
        QAction.__init__(self, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.form = form
        self.triggered.connect(self.runPointTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.pointClick )
        self.layer = layer

    def runPointTool(self):
        self.canvas.setMapTool(self.tool)

    def pointClick(self, point):
        self.layer.startEditing()
        fields = self.layer.pendingFields()
        provider = self.layer.dataProvider()
        self.dialoginstance = self.form.dialogInstance()

        self.binder = FormBinder(self.layer, self.dialoginstance)

        self.feature = QgsFeature()
        self.feature.setGeometry( QgsGeometry.fromPoint( point ) )

        for id, field in fields.items():
            if field.name() == "UniqueID":
                # HACK At the moment we can't rely on the the MS SQL Driver to use correct default values
                # so we must create our own UUID at the moment.  Checks for a column call UniqueID and gives it a UUID
                uuidstring = str(uuid.uuid1())
                log(str(uuidstring))
                self.feature.addAttribute( id, uuidstring )
            else:
                self.feature.addAttribute( id, provider.defaultValue( id ) )

        self.binder.bindFeature(self.feature)
        #HACK Hardcoded
        self.dialoginstance.selectAction.pressed.connect(self.selectSingleFromMap)
        self.dialoginstance.accepted.connect(self.dialogAccept)
        self.dialoginstance.setModal(True)
        self.dialoginstance.show()


    def selectSingleFromMap(self):
        self.emitTool = QgsMapToolEmitPoint(self.canvas)
        self.emitTool.canvasClicked.connect(self.featureSelected)
        self.canvas.setMapTool(self.emitTool)
        self.dialoginstance.hide()
        
    def featureSelected(self, point, button):
        curdir = os.path.dirname(self.form.__file__)
        path =os.path.join(curdir,'settings.ini')
        settings = QSettings(path, QSettings.IniFormat)
        layername = settings.value("selectAction/layer").toString()
        column = settings.value("selectAction/column").toString()
        log(layername)
        log(column)
        for layer in self.canvas.layers():
            log("Looking at %s " % layer.name())
            if layer.type() == QgsMapLayer.RasterLayer:
                continue
                
            if layer.name() == layername:
                searchRadius = self.canvas.extent().width() * ( 0.5 / 100.0)
                log("Finding Featues at %s with radius of %s" % (point, searchRadius))
                rect = QgsRectangle()
                rect.setXMinimum( point.x() - searchRadius );
                rect.setXMaximum( point.x() + searchRadius );
                rect.setYMinimum( point.y() - searchRadius );
                rect.setYMaximum( point.y() + searchRadius );

                layer.select( layer.pendingAllAttributesList(), rect, True, True)
                feature = QgsFeature()
                layer.nextFeature(feature)
                index = layer.fieldNameIndex(column)
                value = feature.attributeMap()[index].toString()
                #HACK Hardcoded
                self.dialoginstance.TextField.setText(value)
                break
        
        self.dialoginstance.show()
        
    def dialogAccept(self):
        log("Saving values back")
        feature = self.binder.unbindFeature(self.feature)
        log("New feature %s" % feature)
        for value in feature.attributeMap().values():
            log("New value %s" % value.toString())

        self.layer.addFeature( self.feature )
        self.canvas.refresh()
        self.layer.commitChanges()
        self.runPointTool()