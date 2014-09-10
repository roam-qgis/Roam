from PyQt4.QtGui import  QCheckBox

from roam.editorwidgets.core import EditorWidget, registerwidgets


class CheckboxWidget(EditorWidget):
    widgettype = 'Checkbox'
    def __init__(self, *args, **kwargs):
        super(CheckboxWidget, self).__init__(*args, **kwargs)
        self.validationstyle += """QCheckBox[required=true]
                                {border-radius: 5px; background-color: rgba(255, 221, 48,150);}
                                QCheckBox[ok=true]
                                {border-radius: 5px; background-color: rgba(200, 255, 197, 150); }
                                QGroupBox::title[required=true]
                                {border-radius: 5px; background-color: rgba(255, 221, 48,150);}
                                QGroupBox::title[ok=true]
                                { border-radius: 5px; background-color: rgba(200, 255, 197, 150); }"""

    def createWidget(self, parent):
        return QCheckBox(parent)

    def initWidget(self, widget):
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
