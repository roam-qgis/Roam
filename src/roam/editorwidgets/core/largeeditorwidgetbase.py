from PyQt5.QtCore import pyqtSignal

from roam.editorwidgets.core import EditorWidget


class LargeEditorWidget(EditorWidget):
    """
    A large editor widget will take up all the UI before the action is finished.
    These can be used to show things like camera capture, drawing pads, etc

    The only thing this class has extra is a finished signal and emits that once input is complete.
    """
    finished = pyqtSignal(object)
    cancel = pyqtSignal(object, int)

    def __init__(self, *args, **kwargs):
        EditorWidget.__init__(self, *args, **kwargs)

    def emit_finished(self):
        self.finished.emit(self.value())

    def emit_cancel(self, reason=None, level=1):
        self.cancel.emit(reason, level)

    def before_load(self):
        """
        Called before the widget is loaded into the UI
        """
        pass

    def after_load(self):
        """
        Called after the widget has been loaded into the UI
        """
        pass