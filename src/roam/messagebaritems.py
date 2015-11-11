import os
import traceback

from PyQt4.QtGui import (QApplication,
                         QPushButton,
                         QIcon,
                         QWidget,
                         QDialog,
                         QToolButton,
                         QFont)
from PyQt4.QtCore import QEvent, QObject, Qt, QSize, pyqtSignal

from qgis.gui import QgsMessageBarItem, QgsMessageBar
from fabricate import _after

import roam_style

import roam.htmlviewer
import roam.utils
import roam.resources_rc


class MessageBar(QWidget):
    def __init__(self, parent=None):
        super(MessageBar, self).__init__(parent)
        self.items = []
        self.messagestack = []

    def pushMessage(self, title, text=None, level=QgsMessageBar.INFO, duration=0, extrainfo=None):
        item = ClickableMessage(title, text, level, duration, extrainfo, self.parent())
        self.messagestack.append(item)
        item.show()

    def pushItem(self, item):
        item.setParent(self.parent())
        self.messagestack.append(item)
        item.show()

    def popWidget(self):
        try:
            item = self.messagestack.pop()
            item.deleteLater()
        except IndexError:
            pass

    def pushError(self, text, extrainfo):
        self.pushMessage(QApplication.translate('MessageBarItems', 'Oops', None,
                                                QApplication.UnicodeUTF8),
                         text, QgsMessageBar.CRITICAL, extrainfo=extrainfo)


class ClickableMessage(roam.htmlviewer.HtmlViewerWidget):
    def __init__(self, title=None, text=None, level=QgsMessageBar.INFO, duration=0, extrainfo=None, parent=None):
        super(ClickableMessage, self).__init__(parent)
        self.parent().installEventFilter(self)
        self.extrainfo = extrainfo
        self.template = "notice"
        self.level = level
        if level == QgsMessageBar.CRITICAL:
            self.template = "error"

        self.data = {}
        self.data['title'] = self.template.upper()
        self.data["info"] = self.extrainfo
        self.data['message_level'] = level
        self.frame.setProperty("level", level)
        self.setStyleSheet("""
            /* INFO */
            QFrame[level="0"] {
                border: 5px solid #b9cfe4;
            }

            /* WARNING */
            QFrame[level="1"] {
                border: 5px solid #e0aa00;
            }

            /* CRITICAL */
            QFrame[level="2"] {
                border: 5px solid #9b3d3d;
            }

            /* SUCCESS */
            QFrame[level="3"] {
                border: 5px solid green;
            }
        """)

    def setParent(self, widget):
        super(ClickableMessage, self).setParent(widget)
        self.parent().installEventFilter(self)

    def load_content(self):
        self.showHTML(self.template, self.level, **self.data)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.showEvent(None)

        return super(ClickableMessage, self).eventFilter(object, event)

    def showEvent(self, event):
        self.load_content()
        self.resize(500, 300)
        width = self.parent().geometry().size().width() - self.width() - 20
        self.move(width, 0)


class MissingLayerItem(ClickableMessage):
    def __init__(self, layers, parent=None):
        super(MissingLayerItem, self).__init__(level=QgsMessageBar.WARNING, parent=parent)
        message = "Seems like {} didn't load correctly".format(roam.utils._pluralstring('layer', len(layers)))
        self.template = "missing_layers"
        self.data["message"] = message
        self.data["missinglayers"] = layers
        self.data['title'] = "Failed to load"


class UndoMessageItem(ClickableMessage):
    undo = pyqtSignal(object, object)

    def __init__(self, title, message, form, feature, parent=None):
        super(UndoMessageItem, self).__init__(parent=parent)
        self.setLevel(QgsMessageBar.INFO)
        self.setDuration(3)
        self.setTitle(title)
        self.button = QPushButton(message)
        self.button.clicked.connect(self.undo)
        self.layout().insertWidget(0, self.button)
        self.form = form
        self.feature = feature

    def undo(self):
        self.undo.emit(self.form, self.feature)
