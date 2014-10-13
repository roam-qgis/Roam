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
import roam.resources_rc

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
        self.items = []

        closebutton = self.findChild(QToolButton)
        closebutton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        closebutton.setIcon(QIcon(":/icons/cancel"))
        closebutton.clicked.disconnect()
        closebutton.clicked.connect(self.popWidget)

        self.parent().installEventFilter(self)

    def showEvent(self, event):
        self.resize(QSize(self.parent().geometry().size().width(), 50))
        self.move(0, self.parent().geometry().size().height() - self.height())
        self.raise_()

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.showEvent(None)

        return super(MessageBar, self).eventFilter(object, event)

    def pushMessage(self, title, text=None, level=QgsMessageBar.INFO, duration=0, extrainfo=None):
        item = ClickableMessage(title, text, level, duration, extrainfo)
        if level == QgsMessageBar.INFO:
            item.setIcon(QIcon(":/icons/info"))
        elif level == QgsMessageBar.WARNING:
            item.setIcon(QIcon(":/icons/warning"))
        elif level == QgsMessageBar.CRITICAL:
            item.setIcon(QIcon(":/icons/error"))

        # Icon doesn't take unless you call set title again. :S
        item.setTitle(title)
        self.pushItem(item)
        self.setStyleSheet(item.getStyleSheet())

    def popWidget(self):
        super(MessageBar, self).popWidget()

        # HACK Gross hack because QgsMessageBar doesn't expose the current item
        # and does it's own stylesheet thing.  Yuck!
        items = self.findChildren(ClickableMessage)
        try:
            item = items[-1]
        except IndexError:
            self.hide()
            return

        if not item:
            self.hide()
            return

        print item.level()
        print item.getStyleSheet()
        self.setStyleSheet(item.getStyleSheet())

    def pushError(self, text, extrainfo):
        self.pushMessage(QApplication.translate('MessageBarItems', 'Oops', None,
                                                QApplication.UnicodeUTF8),
                         text, QgsMessageBar.CRITICAL, extrainfo=extrainfo)


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

    def getStyleSheet(self):
        if self.level() == QgsMessageBar.CRITICAL:
            return """QgsMessageBar { border: 5px solid #9b3d3d; }"""
        elif self.level() == QgsMessageBar.WARNING:
            return """QgsMessageBar { border: 5px solid #e0aa00; }"""
        elif self.level() == QgsMessageBar.INFO:
            return """QgsMessageBar { border: 5px solid #b9cfe4; }"""


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




