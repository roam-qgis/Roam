from qgis.PyQt.QtCore import QObject, pyqtSignal

# Doing this is a bit gross but meh.


class _Events(QObject):
    deleteForm = pyqtSignal()
    projectCreated = pyqtSignal(object)
    formCreated = pyqtSignal(object)

    def emit_projectCreated(self, project):
        self.projectCreated.emit(project)

    def emit_formCreated(self, form):
        self.formCreated.emit(form)


ConfigEvents = _Events()
