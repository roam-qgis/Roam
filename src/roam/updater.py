from PyQt4.QtCore import QObject, bin

class ProjectUpdater(QObject):
    foundProjects = pyqtSignal(object)