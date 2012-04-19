from PyQt4 import QtGui
from ui_concept import Ui_WaterForm

__formName__ = "Concept Form"
__layerName__ = "ProofConcept"
__mapTool__ = None
__mapToolType__ = "POINT"

def dialogInstance():
    return MyDialog()

class MyDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_WaterForm()
        self.ui.setupUi(self)