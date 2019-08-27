import os
import traceback

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QEvent, pyqtSignal

from qgis.core import Qgis
from qgis.gui import QgsMessageBar

import roam.htmlviewer
import roam.resources_rc


class MessageBar():
    def __init__(self, parent=None):
        self.parent = parent
        self.items = []
        self.messagestack = []

    def pushMessage(self, title, text=None, level=Qgis.Info, duration=0, extrainfo=None):
        item = ClickableMessage(title, text, level, duration, extrainfo)
        self.pushItem(item)

    def pushItem(self, item):
        item.setParent(self.parent)
        self.messagestack.append(item)
        item.show()

    def popWidget(self):
        try:
            item = self.messagestack.pop()
            item.deleteLater()
        except IndexError:
            pass

    def pushError(self, *exinfo):
        item = ExceptionItem(*exinfo)
        self.pushItem(item)


class ClickableMessage(roam.htmlviewer.HtmlViewerWidget):
    def __init__(self, title=None, text=None, level=Qgis.Info, duration=0, extrainfo=None, parent=None):
        super(ClickableMessage, self).__init__(parent)
        self.extrainfo = extrainfo
        self.template = "notice"
        self.level = level
        if level == Qgis.Critical:
            self.template = "error"

        self.data = {}
        self.data['title'] = title
        if not title:
            self.data['title'] = self.template.title()

        self.data["message"] = text
        if extrainfo:
            self.data["info"] = self.extrainfo.replace(r"\n", "<br>")
        else:
            self.data['info'] = ""
        self.data['message_level'] = level
        self.frame.setProperty("level", level)
        self.setStyleSheet("""
            /* INFO */
            QFrame[level="0"] {
                border: 2px solid #b9cfe4;
            }

            /* WARNING */
            QFrame[level="1"] {
                border: 2px solid #e0aa00;
            }

            /* CRITICAL */
            QFrame[level="2"] {
                border: 2px solid #9b3d3d;
            }

            /* SUCCESS */
            QFrame[level="3"] {
                border: 2px solid green;
            }
        """)

    def setParent(self, widget):
        super(ClickableMessage, self).setParent(widget)
        self.parent().installEventFilter(self)

    def load_content(self):
        self.showHTML(self.template, self.level, **self.data)
        self.resize(500, self.height())

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.showEvent(None)

        return super(ClickableMessage, self).eventFilter(object, event)

    def showEvent(self, event):
        self.load_content()
        width = self.parent().geometry().size().width() - self.width() - 20
        self.move(width, 0)


class MissingLayerItem(ClickableMessage):
    def __init__(self, layers, parent=None):
        super(MissingLayerItem, self).__init__(level=Qgis.Warning, parent=parent)
        self.template = "missing_layers"
        self.data["missinglayers"] = layers
        self.data['title'] = "Layers failed to load"


class ExceptionItem(ClickableMessage):
    def __init__(self, *exinfo):
        super(ExceptionItem, self).__init__(level=Qgis.Critical)
        message = "Something has gone wrong."
        self.template = "exception"
        self.data["message"] = message
        info = traceback.format_exception(*exinfo)
        error = info[-1]
        self.data["stack"] = "".join(info).replace(r"\n", "<br>")
        self.data['title'] = message
        self.data['error'] = error


class UndoMessageItem(ClickableMessage):
    undo = pyqtSignal(object, object)

    def __init__(self, title, message, form, feature, parent=None):
        super(UndoMessageItem, self).__init__(parent=parent)
        self.setLevel(Qgis.Info)
        self.setDuration(3)
        self.setTitle(title)
        self.button = QPushButton(message)
        self.button.clicked.connect(self.undo)
        self.layout().insertWidget(0, self.button)
        self.form = form
        self.feature = feature

    def undo(self):
        self.undo.emit(self.form, self.feature)
