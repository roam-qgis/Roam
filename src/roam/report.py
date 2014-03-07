import os
import sys
import subprocess
import types
import json

from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, QObject, QSize, QEvent, QProcess, Qt, QPyNullVariant, QRegExp
from PyQt4.QtGui import (QWidget,
                         QDialogButtonBox,
                         QStatusBar,
                         QLabel,
                         QGridLayout,
                         QToolButton,
                         QIcon,
                         QLineEdit,
                         QPlainTextEdit,
                         QComboBox,
                         QDateTimeEdit,
                         QBoxLayout,
                         QSpacerItem,
                         QFormLayout)

from qgis.core import QgsFields, QgsFeature, QgsGPSConnectionRegistry

from roam.editorwidgets.core import WidgetsRegistry, EditorWidgetException
from roam import utils
from roam.flickwidget import FlickCharm
from roam.structs import CaseInsensitiveDict

settings = {}

style = """
            QCheckBox::indicator {
                 width: 40px;
                 height: 40px;
             }

            * {
                font: 20px "Segoe UI" ;
            }

            QLabel {
                color: #4f4f4f;
            }

            QDialog { background-color: rgb(255, 255, 255); }
            QScrollArea { background-color: rgb(255, 255, 255); }

            QPushButton {
                border: 1px solid #e1e1e1;
                 padding: 6px;
                color: #4f4f4f;
             }

            QPushButton:hover {
                border: 1px solid #e1e1e1;
                 padding: 6px;
                background-color: rgb(211, 228, 255);
             }

            QCheckBox {
                color: #4f4f4f;
            }

            QComboBox {
                border: 1px solid #d3d3d3;
            }

            QComboBox::drop-down {
            width: 30px;
            }
"""



def nullcheck(value):
    if isinstance(value, QPyNullVariant):
        return None
    else:
        return value


def buildfromui(uifile, base):
    widget = uic.loadUi(uifile, base)
    return installflickcharm(widget)

def installflickcharm(widget):
    """
    Installs the flick charm on every widget on the form.
    """
    widget.charm = FlickCharm()
    for child in widget.findChildren(QWidget):
        widget.charm.activateOn(child)
    return widget


class RejectedException(Exception):
    WARNING = 1
    ERROR = 2

    def __init__(self, message, level=WARNING):
        super(RejectedException, self).__init__(message)
        self.level = level


class ReportBase(QWidget):
    requiredfieldsupdated = pyqtSignal(bool)
    formvalidation = pyqtSignal(bool)
    helprequest = pyqtSignal(str)
    showwidget = pyqtSignal(QWidget)
    loadform = pyqtSignal()
    rejected = pyqtSignal(str)
    enablesave = pyqtSignal(bool)


    def __init__(self, config, parent=None):
        super(ReportBase, self).__init__(parent)
        self.config = config


    def _installeventfilters(self, widgettype):
        for widget in self.findChildren(widgettype):
            widget.installEventFilter(self)

    def eventFilter(self, object, event):
        # Hack I really don't like this but there doesn't seem to be a better way at the
        # moment.
        if event.type() == QEvent.FocusIn and settings.get('keyboard', True):
            cmd = r'C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe'
            os.startfile(cmd)

        return False

    def setupui(self):
        """
        Setup the widget in the form
        """

class Report(ReportBase):
    """
    You may override this in project __init__.py module in order to add custom logic in the following
    places:

        - loading
        - loaded
        - save
        - close


    class MyModule(Report):
        def __init__(self, widget, formconfig):
            super(MyModule, self).__init__(widget, formconfig)

        def save(self):
            ....


    In order to register your report class you need to call `report.registerform` from the init_report method
    in your report module

    def init_report(report):
        report.registerReport(MyModule)


  
    """

    def __init__(self, reportconfig, reportparent=None):
        super(Report, self).__init__(config=reportconfig, parent=reportparent)


    @classmethod
    def from_factory(cls, config, folder, parent=None):
        """
        Create a report widget from the given Roam report.
        :param report: A Roam report
        :param parent:
        :return:
        """
 
        report = cls(reportconfig=config, reportparent=parent)

        utils.log("folder " + folder)        
        uifile = os.path.join(folder, "report.ui")
        report = buildfromui(uifile, base=report)

        report.setContentsMargins(3, 0, 3, 0)
        reportstyle = style
        reportstyle += report.styleSheet()
        report.setStyleSheet(reportstyle)
        report.setProperty('report', report)
        report.setupui()
        report.uisetup()
        return report

    def toNone(self, value):
        """
        Convert the value to a None type if it is a QPyNullVariant, because noone likes that
        crappy QPyNullVariant type.

        :return: A None if the the value is a instance of QPyNullVariant. Returns the given value
                if not.
        """
        return nullcheck(value)

    def uisetup(self):
        """
        Called when the UI is fully constructed.  You should connect any signals here.
        """
        pass

    def load(self):
        """
        Called before the report is loaded. This method can be used to do pre checks and halt the loading of the report
        if needed.

        When implemented, this method should always return a tuple with a pass state and a message.

        Calling self.reject("Your message") will stop the opening of the report and show the message to the user.

        """
        pass

    def loaded(self):
        pass

    def accept(self):
        return True

    def cancelload(self, message=None, level=RejectedException.WARNING):
        raise RejectedException(message, level)

    def saveenabled(self, enabled):
        self.enablesave.emit(enabled)


