from qgis.PyQt.QtWidgets import QDialog, QScrollArea, QGraphicsScene, QGraphicsView
from qgis.PyQt.QtCore import QUrl, QEvent, Qt, QSize
from qgis.PyQt.QtWebKitWidgets import QWebPage, QGraphicsWebView

from roam.api.utils import install_touch_scroll
from roam.api.events import RoamEvents
from roam.ui.uifiles import (helpviewer_widget, helpviewer_base,
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

        self.view = QGraphicsView()
        self.webView = QGraphicsWebView()
        self.scene = QGraphicsScene()
        self.webView.setResizesToContents(True)
        self.view.setScene(self.scene)
        self.scene.addItem(self.webView)

        self.webView.linkClicked.connect(RoamEvents.openurl.emit)
        self.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        install_touch_scroll(self.view)
        self.layout().addWidget(self.view)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.setsize()
        elif event.type() == QEvent.MouseButtonPress:
            self.close()
        return object.eventFilter(object, event)

    def setsize(self):
        width = self.parent().width() * 50 / 100
        self.resize(width, self.parent().height())
        self.move(self.parent().width() - self.width() - 1, 1)

    def show(self):
        super(HelpPage, self).show()
        self.setsize()
        self.setFocus(Qt.PopupFocusReason)

    def setHelpPage(self, helppath):
        self.webView.load(QUrl.fromLocalFile(helppath))
