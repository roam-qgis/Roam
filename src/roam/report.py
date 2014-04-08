import os

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, QEvent 
from PyQt4.QtGui import QWidget, QLabel, QComboBox

from roam import utils
from roam.flickwidget import FlickCharm

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

    def __init__(self, folder, config, errorbar, parent=None):
        super(ReportBase, self).__init__(parent)
        self.settings = config
        self.bar = errorbar


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


class Report(ReportBase):

    """
    You may override this in project __init__.py module 
    in order to add custom logic in the following
    places:

        - uisetup

    class MyModule(Report):
        def __init__(self, widget, formconfig):
            super(MyModule, self).__init__(widget, formconfig)

        def uisetup(self):
            

    In order to register your report class you

    need to call report.registerform from the init_report method
    in your report module

    def init_report(report):
        report.registerReport(MyModule)
  
    """
    def __init__(self, folder, config, errorbar, parent=None):
        super(Report, self).__init__(folder, config, errorbar, parent)

    @classmethod
    def from_factory(cls, config, folder, errorbar, parent=None):
        """
        Create a report widget from the given Roam report.
        """
        report = cls(folder, config, errorbar, parent)

        uifile = os.path.join(folder, "report.ui")
        report = buildfromui(uifile, base=report)

        report.setContentsMargins(3, 0, 3, 0)
        reportstyle = style
        reportstyle += report.styleSheet()
        report.setStyleSheet(reportstyle)
        report.setProperty('report', report)
        report.uisetup()
        return report


    def uisetup(self):
        """
        Called when the UI is constructed.  
	Connect any signals here and load widgets with data.
        """
        pass




