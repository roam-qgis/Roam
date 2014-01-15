from PyQt4.QtGui import QToolBar
from PyQt4.QtCore import Qt


class MenuToolbar(QToolBar):
    def __init__(self, parent=None):
        super(MenuToolbar, self).__init__(parent)

    def mouseDoubleClickEvent(self, *args, **kwargs):
        style = self.toolButtonStyle()
        if style == Qt.ToolButtonIconOnly:
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        else:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)

        super(MenuToolbar, self).mouseDoubleClickEvent(*args, **kwargs)
