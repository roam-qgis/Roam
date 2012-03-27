__author__="WOODROWN"
__date__ ="$21/03/2012 2:20:26 PM$"

from PyQt4 import QtCore, QtGui
from ui_waterForm import Ui_WaterForm

__formName__ = "Water Form"
__layerName__ = "waterpoint"
__mapTool__ = None
__mapToolType__ = "POINT"

def dialogInstance():
    return WaterCaptureForm()

def formOpened(formInstance, qgsfeture, layer, iface):
    """
    Method called after form is bound.
    """
    pass

class WaterCaptureForm(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_WaterForm()
        self.ui.setupUi(self)

