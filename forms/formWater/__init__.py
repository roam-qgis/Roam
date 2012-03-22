__author__="WOODROWN"
__date__ ="$21/03/2012 2:20:26 PM$"

from PyQt4 import QtCore, QtGui
from ui_waterForm import Ui_WaterForm

def name():
    return "Water Form"

def init(qgsfeature):
    form = WaterCaptureForm(qgsfeature)
    form.exec_()

def mapToolType():
    return "POINT"

class WaterCaptureForm(QtGui.QDialog):
    def __init__(self, qgsfeature):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_WaterForm()
        self.ui.setupUi(self)
        self.feature = qgsfeature
