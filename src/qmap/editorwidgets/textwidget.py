from PyQt4.QtGui import QLineEdit

from qmap.editorwidgets.core import WidgetFactory, EditorWidget


class TextWidget(EditorWidget):
    def __init__(self, *args):
        super(TextWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QLineEdit(parent)

    def initWidget(self, widget):
        widget.textChanged.connect(self.validate)

    def validate(self, *args):
        if not self.value():
            self.raisevalidationupdate(False)
        else:
            self.raisevalidationupdate(True)

    def setvalue(self, value):
        # Not the best way but should cover most use cases
        # for now
        value = value or ''
        value = str(value)
        try:
            self.widget.setPlainText(value)
        except AttributeError:
            self.widget.setText(value)

    def value(self):
        try:
            return self.widget.toPlainText()
        except AttributeError:
            return self.widget.text()

factory = WidgetFactory("Text", TextWidget, None)
