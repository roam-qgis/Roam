from PyQt4.QtCore import Qt, QPoint
from PyQt4.QtGui import QDialog, QGridLayout
from PyQt4.QtWebKit import QWebPage, QWebView


class PopDownReport(QDialog):
    def __init__(self, parent):
        super(PopDownReport, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.web = QWebView()
        self.resize(400, 400)
        self.layout().addWidget(self.web)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint)

    def updateHTML(self, html):
        self.web.setHtml(html)
        self.web.triggerPageAction(QWebPage.MoveToEndOfDocument)
        
    def clear(self):
        self.web.setHtml("No Sync in progress")
        
    def updatePosition(self):
        point = self.parent().rect().bottomRight()
        newpoint = self.parent().mapToGlobal(point - QPoint(self.size().width(),0))
        self.move(newpoint)

    def showEvent(self, event):
        self.updatePosition()
