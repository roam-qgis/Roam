from PointTool import PointTool, log
from PyQt4.QtGui import QAction
from qgis.core import *
from qgis.gui import *
import uuid
from forms.ListFeatureForm import ListFeaturesForm
from FormBinder import FormBinder

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
        dialoginstance = self.form.dialogInstance()

        binder = FormBinder(self.layer, dialoginstance)

        feature = QgsFeature()
        feature.setGeometry( QgsGeometry.fromPoint( point ) )


        for id, field in fields.items():
            if field.name() == "UniqueID":
                # HACK At the moment we can't rely on the the MS SQL Driver to use correct default values
                # so we must create our own UUID at the moment.  Checks for a column call UniqueID and gives it a UUID
                uuidstring = str(uuid.uuid1())
                log(str(uuidstring))
                feature.addAttribute( id, uuidstring )
            else:
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