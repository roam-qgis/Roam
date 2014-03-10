from PyQt4.QtCore import *
from PyQt4.QtGui import *

from roam.ui.uifiles import report_widget, report_base
from roam.flickwidget import FlickCharm


class DefaultError(Exception):
    pass

class ReportWidget(report_widget, report_base):
    """
    """
    closed = pyqtSignal()

    def __init__(self, bar, parent=None):
        super(ReportWidget, self).__init__(parent)
        self.setupUi(self)
        self.project = None
        self.bar = bar

        self.flickwidget = FlickCharm()
        self.flickwidget.activateOn(self.scrollArea)

        toolbar = QToolBar()
        size = QSize(48, 48)
        toolbar.setIconSize(size)
        style = Qt.ToolButtonTextUnderIcon
        toolbar.setToolButtonStyle(style)
        self.actionClose.triggered.connect(self.closeReport)

        spacer = QWidget()
        spacer2 = QWidget()
        spacer2.setMinimumWidth(20)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        toolbar.addWidget(spacer)
        toolbar.addAction(self.actionClose)
        toolbar.addWidget(spacer2)
        self.layout().insertWidget(0, toolbar)

    def closeReport(self):
        self.clear()
        self.closed.emit()

    def setwidget(self, widget):
        self.clearcurrentwidget()
        self.scrollAreaWidgetContents.layout().insertWidget(0, widget)

    def clear(self):
        self.clearcurrentwidget()

    def clearcurrentwidget(self):
        item = self.scrollAreaWidgetContents.layout().itemAt(0)
        if item and item.widget():
            widget = item.widget()
            widget.setParent(None)
            widget.deleteLater()

    def openReport(self, project):
	"""
	opens report widget for a given project
	"""
	self.report = project.report.create_report()
	self.setwidget(self.report)

