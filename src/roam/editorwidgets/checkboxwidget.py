from PyQt4.QtGui import QCheckBox

from roam.editorwidgets.core import EditorWidget, registerwidgets


class CheckboxWidget(EditorWidget):
    widgettype = 'Checkbox'

    def __init__(self, *args, **kwargs):
        super(CheckboxWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return QCheckBox(parent)

    def initWidget(self, widget, config):
        widget.toggled.connect(self.emitvaluechanged)
        widget.toggled.connect(self.validate)

    def validate(self, *args):
        return self.widget.isChecked()

    def setvalue(self, value):
        checkedvalue = self.config['checkedvalue']
        checked = str(value) == checkedvalue or False
        self.widget.setChecked(checked)

    def value(self):
        if self.widget.isChecked():
            return self.config['checkedvalue']
        else:
            return self.config['uncheckedvalue']
