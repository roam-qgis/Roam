from PyQt4.QtGui import  QCheckBox

from qmap.editorwidgets.core import WidgetFactory, EditorWidget
from qmap import nullcheck

class CheckboxWidget(EditorWidget):
    def __init__(self, *args):
        super(CheckboxWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QCheckBox(parent)

    def setvalue(self, value):
        checkedvalue = self.config['checkedvalue']
        checked = str(value) == checkedvalue or False
        self.widget.setChecked(checked)

    def value(self):
        if self.widget.isChecked():
            return self.config['checkedvalue']
        else:
            return self.config['uncheckedvalue']

factory = WidgetFactory("Checkbox", CheckboxWidget, None)
