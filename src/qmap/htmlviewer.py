import os
    
from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QDialog, QWidget, QGridLayout, QPixmap
from PyQt4.QtWebKit import QWebView, QWebPage

import utils

def showHTMLReport(title, html, images):
    dialog = HtmlViewerDialog(title)
    dialog.showHTML(html, images)
    dialog.exec_()

class HtmlViewerDialog(QDialog):
    def __init__(self, title, parent=None):
        super(HtmlViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.htmlviewer = HtmlViewerWidget(self)
        self.layout().addWidget(self.htmlviewer)
        
    def showHTML(self, html, images):
        self.htmlviewer.showHTML(html, images)

class HtmlViewerWidget(QWidget):
    def __init__(self, parent):
        super(HtmlViewerWidget, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.view = QWebView(linkClicked=self.openimage)
        self.view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.layout().addWidget(self.view)
        
    def showHTML(self, html, images):
        self.images = images
        base = os.path.dirname(os.path.abspath(__file__))
        baseurl = QUrl.fromLocalFile(base + '\\')
        self.view.setHtml(html, baseurl)
        
    def openimage(self, url):
        key = url.toString().lstrip('file://')
        try:
            data, imagetype = self.images[os.path.basename(key)]
        except KeyError:
            return
        pix = QPixmap()
        if imagetype == 'base64':
            pix.loadFromData(data)
        else:
            pix.load(data)
        utils.openImageViewer(pix)