from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QUrl

from uifiles import (helpviewer_widget, helpviewer_base,
                     helppage_widget, helppage_base)

class HelpViewDialog(helpviewer_widget, helpviewer_base):
    def __init__(self, startimage=None):
        super(HelpViewDialog, self).__init__()
        QDialog.__init__(self)
        self.setupUi(self)
        
    def loadFile(self, htmlfile):
        self.webView.load(QUrl.fromLocalFile(htmlfile))
        
class HelpPage(helppage_widget, helppage_base):
    def __init__(self, parent=None):
        super(HelpPage, self).__init__(parent)
        self.setupUi(self)
        
    def setHelpPage(self, helppath):
        self.webView.load(QUrl.fromLocalFile(helppath))

        
