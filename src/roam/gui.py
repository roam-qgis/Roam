from PyQt4.QtGui import QToolBar
from PyQt4.QtCore import Qt

from roam.gpswidget import GPSWidget
from roam.syncwidget import SyncWidget
from roam.settingswidget import SettingsWidget
from roam.listmodulesdialog import ProjectsWidget


class HideableToolbar(QToolBar):
    def __init__(self, parent=None):
        super(HideableToolbar, self).__init__(parent)
        self.startstyle = None

    def mouseDoubleClickEvent(self, *args, **kwargs):
        style = self.toolButtonStyle()
        if style != self.startstyle:
            self.setToolButtonStyle(self.startstyle)
        else:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)

        super(HideableToolbar, self).mouseDoubleClickEvent(*args, **kwargs)

    def setToolButtonStyle(self, style):
        if not self.startstyle:
            self.startstyle = style

        super(HideableToolbar, self).setToolButtonStyle(style)
