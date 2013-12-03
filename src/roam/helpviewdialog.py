from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QUrl, QEvent, Qt

from roam.uifiles import (helpviewer_widget, helpviewer_base,
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
        if self.parent():
            self.parent().installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.setsize()
        return object.eventFilter(object, event)

    def setsize(self):
        width = self.parent().width() * 30 / 100
        self.resize(width, self.parent().height())
        self.move(self.parent().width() - self.width() -1, 1)

    def show(self):
        self.setsize()
        self.setFocus(Qt.PopupFocusReason)
        super(HelpPage, self).show()

    def focusOutEvent(self, event):
        self.close()

    def setHelpPage(self, helppath):
        self.webView.load(QUrl.fromLocalFile(helppath))

        
