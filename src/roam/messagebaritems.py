import os
import traceback

from PyQt4.QtGui import (QApplication, 
                         QPushButton, 
			 QIcon, 
			 QWidget, 
			 QDialog, 
			 QToolButton, 
			 QFont)
from PyQt4.QtCore import QEvent, QObject, Qt, QSize

from qgis.gui import QgsMessageBarItem, QgsMessageBar

import roam.htmlviewer
import roam.utils

style = """QPushButton {
        border: 1px solid #e1e1e1;
         padding: 6px;
        color: #4f4f4f;
     }

    QPushButton:hover {
        border: 1px solid #e1e1e1;
         padding: 6px;
        background-color: rgb(211, 228, 255);
     }"""

htmlpath = os.path.join(os.path.dirname(__file__), "templates/error.html")


class MessageBar(QgsMessageBar):
    def __init__(self, parent=None):
        super(MessageBar, self).__init__(parent)

        closebutton = self.findChild(QToolButton)
        closebutton.setText(QApplication.translate('MessageBarItems','Dismiss', None, QApplication.UnicodeUTF8))
        closebutton.setToolButtonStyle(Qt.ToolButtonTextOnly)
        closebutton.setStyleSheet(style)

    def showEvent(self, event):
        self.resize(QSize(self.parent().geometry().size().width(), 50))

    def pushMessage(self, title, text=None, level=QgsMessageBar.INFO, duration=0, extrainfo=None):
        item = ClickableMessage(title, text, level, duration, extrainfo)
        self.pushItem(item)

    def pushError(self, text, extrainfo):
        item = ClickableMessage(QApplication.translate('MessageBarItems','Oops', None, QApplication.UnicodeUTF8), text, QgsMessageBar.CRITICAL, extrainfo=extrainfo)
        item.setIcon(QIcon(":/icons/sad"))
        self.pushItem(item)

class ClickableMessage(QgsMessageBarItem):
    def __init__(self, title=None, text=None, level=QgsMessageBar.INFO, duration=0, extrainfo=None, parent=None):
        super(ClickableMessage, self).__init__(title, text, level, duration, parent)
        self.installEventFilter(self)
        self.setCursor(Qt.PointingHandCursor)
        self.updatefilters()
        self.extrainfo = extrainfo
        self.title = title

    def updatefilters(self):
        for child in self.findChildren(QWidget):
            if isinstance(child, QPushButton):
                continue

            child.setCursor(Qt.PointingHandCursor)
            child.installEventFilter(self)

    def eventFilter(self, object, event):
        """ Handle mouse click events for disabled widget state """
        if event.type() == QEvent.MouseButtonRelease and self.extrainfo:
            self.showmessage()
            event.accept()

        return super(ClickableMessage, self).eventFilter(object, event)

    def showmessage(self):
        html = self.extrainfo
        data = []
        if self.level() == QgsMessageBar.CRITICAL:
            if isinstance(self.extrainfo, basestring):
                data = {"ERROR": "{}".format(self.extrainfo)}
            else:
                data = {"ERROR": "<br>".join(self.extrainfo)}
            html = htmlpath
            data = data

        roam.htmlviewer.showHTMLReport(title=self.title,
                                       html=html,
                                       data=data,
                                       parent=self.parent())


class MissingLayerItem(ClickableMessage):
    def __init__(self, layers, parent=None):
        super(MissingLayerItem, self).__init__(parent=parent)
        self.setIcon(QIcon(":/icons/sad"))
        message = "Seems like {} didn't load correctly".format(roam.utils._pluralstring('layer', len(layers)))
        self.setText(message)
        self.setLevel(QgsMessageBar.WARNING)
        self.layers = layers
        self.extrainfo = layers
        self.updatefilters()

    def showmessage(self):
        html = ["<h1>Missing Layers</h1>", "<ul>"]
        for layer in self.layers:
            html.append("<li>{}</li>".format(layer))
        html.append("</ul>")
        html = "".join(html)
        roam.htmlviewer.showHTMLReport(title='Missing Layers', html=html, parent=self.parent())




