from point_tool import PointTool, log
from PyQt4.QtGui import QAction, QLabel, QIcon
from qgis.core import *
from qgis.gui import *
import uuid
import os
from dialog_provider import DialogProvider
from utils import log

class AddAction(QAction):
    """
    Add action for adding a new point.  Handles invoking the form for the
    layer.

    @note: This class feels like it knows a little too much.  Maybe move the
           DialogProvider and feature creation logic out.
    """
    def __init__(self, name, iface, layer, icon ):
        QAction.__init__(self, QIcon(icon), "New %s" % name, iface.mainWindow())
        self.iface = iface
        self.layer = layer
        self.toggled.connect(self.setTool)
        
        self.tool = PointTool( iface.mapCanvas() )
        self.tool.mouseClicked.connect( self.pointClick )

        self.dialogprovider = DialogProvider(iface.mapCanvas(), iface)
        self.dialogprovider.accepted.connect(self.setTool)
        self.dialogprovider.rejected.connect(self.setTool)
        self.setCheckable(True)
        
    def pointClick(self, point):
        """
        Add a new feature at the given point location

        point - A QgsPoint at which to create the new feature.
        """
        # TODO move all this up to the QMap class
        layer = self.layer
        fields = layer.pendingFields()
        provider = layer.dataProvider()
        if not layer.isEditable():
            layer.startEditing()
    
        feature = QgsFeature()
        feature.setGeometry( QgsGeometry.fromPoint( point ) )
        feature.initAttributes(fields.count())
        feature.setFields(fields)
        
        for indx in xrange(fields.count()):
            feature[indx] = provider.defaultValue( indx )

        self.dialogprovider.openDialog( feature, layer, False )
        