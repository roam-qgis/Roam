from PointTool import PointTool, log
from PyQt4.QtGui import QAction, QLabel
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
        self.iface = iface
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

        curdir = os.path.dirname(self.form.__file__)
        settingspath =os.path.join(curdir,'settings.ini')
        
        self.binder = FormBinder(self.layer, self.dialoginstance, self.canvas, settingspath)

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
        self.binder.bindSelectButtons()
        self.binder.beginSelectFeature.connect(self.selectingFromMap)
        self.binder.endSelectFeature.connect(self.featureSelected)
        self.dialoginstance.accepted.connect(self.dialogAccept)
        self.dialoginstance.setModal(True)
        self.dialoginstance.show()

    def selectingFromMap(self):
        label = QLabel("Please select a single feature on the map")
        label.setStyleSheet('font: 75 32pt "MS Shell Dlg 2";color: rgb(231, 175, 62);')
        self.messageitem = self.iface.mapCanvas().scene().addWidget(label)
        self.dialoginstance.hide()
        
    def featureSelected(self):     
        self.iface.mapCanvas().scene().removeItem(self.messageitem)
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