from PyQt4.QtGui import QLineEdit, QPlainTextEdit

from roam.editorwidgets.core import EditorWidget, registerwidgets


class TextWidget(EditorWidget):
    widgettype = 'Text'

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

        self.emitvaluechanged()

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

registerwidgets(TextWidget, TextWidget)
