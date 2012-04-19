from PyQt4 import QtGui
from ui_WaterJobSheetDraft1 import Ui_WaterForm

__formName__ = 'Water Job'
__layerName__ = 'waterjobs'
__mapTool__ = None
__mapToolType__ = 'POINT'

def dialogInstance():
    return WaterFormDialog()

class WaterFormDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_WaterForm()
        self.ui.setupUi(self)