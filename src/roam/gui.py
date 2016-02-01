from PyQt4.QtGui import QToolBar
from PyQt4.QtCore import Qt


class HideableToolbar(QToolBar):
    def __init__(self, parent=None):
        super(HideableToolbar, self).__init__(parent)
        self.startstyle = None

    def mouseDoubleClickEvent(self, *args, **kwargs):
        currentstyle = self.toolButtonStyle()

        if self.startstyle is None:
            self.startstyle = currentstyle

        if currentstyle == Qt.ToolButtonIconOnly:
            self.setToolButtonStyle(self.startstyle)
        else:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)

    def setToolButtonStyle(self, style):
        super(HideableToolbar, self).setToolButtonStyle(style)
