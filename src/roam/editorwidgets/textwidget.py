from roam.api import RoamEvents
from PyQt4.QtGui import QLineEdit, QPlainTextEdit
from PyQt4.QtCore import QEvent

from roam.editorwidgets.core import EditorWidget, registerwidgets


class TextWidget(EditorWidget):
    widgettype = 'Text'

    def __init__(self, *args):
        super(TextWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QLineEdit(parent)

    def initWidget(self, widget):
        widget.textChanged.connect(self.emitvaluechanged)
        widget.installEventFilter(self)

    def eventFilter(self, object, event):
        # Hack I really don't like this but there doesn't seem to be a better way at the
        # moment
        if event.type() == QEvent.FocusIn:
            RoamEvents.openkeyboard.emit()
        return False

    def validate(self, *args):
        if not self.value():
            return False
        else:
            return True

    def setvalue(self, value):
        # Not the best way but should cover most use cases
        # for now
        value = value or ''
        value = unicode(value)
        try:
            self.widget.setPlainText(value)
        except AttributeError:
            self.widget.setText(value)

    def value(self):
        try:
            return self.widget.toPlainText()
        except AttributeError:
            return self.widget.text()


class TextBlockWidget(TextWidget):
    widgettype = 'TextBlock'

    def __init__(self, *args):
        super(TextBlockWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QPlainTextEdit(parent)
