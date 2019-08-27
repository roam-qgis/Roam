from qgis.PyQt.QtCore import QObject, pyqtSignal

# Doing this is a bit gross but meh.


class _Events(QObject):
    deleteForm = pyqtSignal()


ConfigEvents = _Events()
