from point_tool import PointTool, log
from PyQt4.QtGui import QAction, QLabel
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
    def __init__(self, name, iface, form, layer, icon ):
        QAction.__init__(self, icon, name, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.form = form
        self.layer = layer
        self.toggled.connect(self.setTool)
        self.tool = PointTool( self.canvas )
        self.tool.mouseClicked.connect( self.pointClick )
        self.fields = self.layer.pendingFields()
        self.provider = self.layer.dataProvider()
        self.dialogprovider = DialogProvider(self.canvas, iface)
        self.dialogprovider.accepted.connect(self.setTool)
        self.dialogprovider.rejected.connect(self.setTool)
        self.setCheckable(True)

    def setTool(self):
        """ 
        Set the current tool as active

        @note: Should be moved out into qmap.py
        """
        self.canvas.setMapTool(self.tool)
        
    def pointClick(self, point):
        """
        Add a new feature at the given point location

        point - A QgsPoint at which to create the new feature.
        """
        if not self.layer.isEditable():
            self.layer.startEditing()
    
        feature = QgsFeature()
        feature.setGeometry( QgsGeometry.fromPoint( point ) )
        feature.initAttributes(self.fields.count())
        feature.setFields(self.fields)
        
        for indx in xrange(self.fields.count()):
            feature[indx] = self.provider.defaultValue( indx )

        self.dialogprovider.openDialog( self.form, feature, self.layer, False )
        