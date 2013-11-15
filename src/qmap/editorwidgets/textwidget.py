from PyQt4.QtGui import QLineEdit

from qmap.editorwidgets.core import WidgetFactory, EditorWidget
from qmap import nullcheck

class TextWidget(EditorWidget):
    def __init__(self, *args):
        super(TextWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QLineEdit(parent)

    def setvalue(self, value):
        # Not the best way but should cover most use cases
        # for now
        try:
            self.widget.setPlainText(value)
        except AttributeError:
            self.widget.setText(value)

    def value(self):
        try:
            return self.widget.toPlainText()
        except AttributeError:
            self.widget.text()

factory = WidgetFactory("Text", TextWidget, None)
