from  ui_helpviewer import Ui_HelpViewer
from PyQt4 import QtCore, QtGui

class HelpViewDialog(QtGui.QDialog):
    def __init__(self, startimage=None):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_HelpViewer()
        self.ui.setupUi(self)
        
    def loadFile(self, htmlfile):
        self.ui.webView.load(QtCore.QUrl.fromLocalFile(htmlfile))

        
