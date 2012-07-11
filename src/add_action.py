from point_tool import PointTool, log
from PyQt4.QtGui import QAction, QLabel
from qgis.core import *
from qgis.gui import *
import uuid
import os
from dialog_provider import DialogProvider

class AddAction(QAction):
    def __init__(self, name, iface, form, layer, icon ):
        QAction.__init__(self, icon, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.form = form
        self.layer = layer
        self.triggered.connect(self.setTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.pointClick )
        self.fields = self.layer.pendingFields()
        self.provider = self.layer.dataProvider()
        self.dialogprovider = DialogProvider(self.canvas, iface)
        self.dialogprovider.accepted.connect(self.setTool)
        self.dialogprovider.rejected.connect(self.setTool)
        self.setCheckable(True)

    def setTool(self):
        self.canvas.setMapTool(self.tool)
        
    def pointClick(self, point):
        if not self.layer.isEditable():
            self.layer.startEditing()
    
        feature = QgsFeature()
        feature.setGeometry( QgsGeometry.fromPoint( point ) )

        for id, field in self.fields.items():
            log(field.name())
            if field.name() == "UniqueID":
                # HACK At the moment we can't rely on the the MS SQL Driver to use correct default values
                # so we must create our own UUID at the moment.  Checks for a column call UniqueID and gives it a UUID
                uuidstring = str(uuid.uuid1())
                feature.addAttribute( id, uuidstring )
            else:
                feature.addAttribute( id, self.provider.defaultValue( id ) )

        self.dialogprovider.openDialog( self.form, feature, self.layer, False )