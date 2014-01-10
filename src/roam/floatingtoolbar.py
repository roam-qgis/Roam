from PyQt4.QtGui import QToolBar
from PyQt4.QtCore import Qt, QSize, QEvent


class FloatingToolBar(QToolBar):
    def __init__(self, position=(0, 0), parent=None):
        super(FloatingToolBar, self).__init__(parent)
        self.setStyleSheet("background-color : transparent; border: 0px;")
        self._position = position
        self.setIconSize(QSize(32, 32))
        self.setMovable(False)
        self.parent().installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.move(*self.position)

        return False

    def show(self):
        self.move(*self.position)
        super(FloatingToolBar, self).show()

    @property
    def position(self):
        if hasattr(self._position, "__call__"):
            return self._position()
        else:
            return self._position
