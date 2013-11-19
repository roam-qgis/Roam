import os
import traceback

from PyQt4.QtGui import QPushButton, QIcon, QWidget, QDialog, QToolButton, QFont
from PyQt4.QtCore import QEvent, QObject, Qt, QSize

from qgis.gui import QgsMessageBarItem, QgsMessageBar

from qmap.popdialog import PopDownReport
from qmap import resources_rc

import qmap.htmlviewer
import qmap.utils

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

htmlpath = os.path.join(os.path.dirname(__file__), "error.html")


class MessageBar(QgsMessageBar):
    def __init__(self, parent=None):
        super(MessageBar, self).__init__(parent)

        closebutton = self.findChild(QToolButton)
        closebutton.setText('Dismiss')
        closebutton.setToolButtonStyle(Qt.ToolButtonTextOnly)
        closebutton.setStyleSheet(style)

    def showEvent(self, event):
        self.resize(QSize(self.parent().geometry().size().width(), 40))

    def pushMessage(self, title, text=None, level=QgsMessageBar.INFO, duration=0):
        item = ClickableMessage(title, text, level, duration)
        self.pushItem(item)


class ClickableMessage(QgsMessageBarItem):
    def __init__(self, title=None, text=None, level=QgsMessageBar.INFO, duration=0, parent=None):
        super(ClickableMessage, self).__init__(title, text, level, duration, parent)
        self.installEventFilter(self)
        self.setCursor(Qt.PointingHandCursor)
        self.updatefilters()

    def updatefilters(self):
        for child in self.findChildren(QWidget):
            if isinstance(child, QPushButton):
                continue

            child.setCursor(Qt.PointingHandCursor)
            child.installEventFilter(self)

    def eventFilter(self, parent, event):
        """ Handle mouse click events for disabled widget state """
        if event.type() == QEvent.MouseButtonRelease:
            self.showmessage()
            event.accept()

        return QObject.eventFilter(self, parent, event)

    def showmessage(self):
        pass


class ErrorMessage(ClickableMessage):
    def __init__(self, execinfo=None, parent=None):
        super(ErrorMessage, self).__init__(parent=parent)
        self.setIcon(QIcon(":/icons/sad"))
        self.setText('Opps something seems to have gone wrong. Click bar for more details')
        self.setLevel(QgsMessageBar.CRITICAL)
        self.execinfo = execinfo
        self.updatefilters()

    def showmessage(self):
        data = {"ERROR": "<br>".join(traceback.format_exception(*self.execinfo))}
        qmap.htmlviewer.showHTMLReport(title='Error',
                                       html=htmlpath,
                                       data=data,
                                       parent=self.parent())


class MissingLayerItem(ClickableMessage):
    def __init__(self, layers, parent=None):
        super(MissingLayerItem, self).__init__(parent=parent)
        self.setIcon(QIcon(":/icons/sad"))
        message = "Seems like {} didn't load correctly".format(qmap.utils._pluralstring('layer', len(layers)))
        self.setText(message)
        self.setLevel(QgsMessageBar.WARNING)
        self.layers = layers
        self.updatefilters()

    def showmessage(self):
        html = ["<h1>Missing Layers</h1>", "<ul>"]
        for layer in self.layers:
            html.append("<li>{}</li>".format(layer))
        html.append("</ul>")
        html = "".join(html)
        qmap.htmlviewer.showHTMLReport(title='Missing Layers', html=html, parent=self.parent())




