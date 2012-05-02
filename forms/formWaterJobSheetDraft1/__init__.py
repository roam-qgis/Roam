from PyQt4 import QtGui
from ui_WaterJobSheetDraft1 import Ui_WaterForm

__formName__ = 'Add new water job'
__layerName__ = 'WaterJobs'
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