from PyQt5.QtWidgets import QToolBar
from PyQt5.QtCore import Qt, pyqtSignal


class HideableToolbar(QToolBar):
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(HideableToolbar, self).__init__(parent)
        self.startstyle = None

    def mouseDoubleClickEvent(self, *args, **kwargs):
        currentstyle = self.toolButtonStyle()
        if currentstyle == Qt.ToolButtonIconOnly:
            self.setSmallMode(False)
        else:
            self.setSmallMode(True)

    def setSmallMode(self, smallmode):
        currentstyle = self.toolButtonStyle()

        if self.startstyle is None:
            self.startstyle = currentstyle

        if not smallmode:
            self.setToolButtonStyle(self.startstyle)
        else:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.stateChanged.emit(smallmode)

    def setToolButtonStyle(self, style):
        super(HideableToolbar, self).setToolButtonStyle(style)
