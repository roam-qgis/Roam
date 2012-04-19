__author__="WOODROWN"
__date__ ="$21/03/2012 2:20:26 PM$"

from PyQt4 import uic, QtCore, QtGui
from ui_concept import Ui_WaterForm
import os
from SDRCDataCapture.utils import Timer

__formName__ = "Concept Form"
__layerName__ = "ProofConcept"
__mapTool__ = None
__mapToolType__ = "POINT"

def dialogInstance():
    with Timer("returning form"):
        return MyDialog()

class MyDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_WaterForm()
        self.ui.setupUi(self)