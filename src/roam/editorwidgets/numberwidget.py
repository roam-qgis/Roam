from PyQt4.QtGui import QDoubleSpinBox

from roam.editorwidgets.core import EditorWidget, registerwidgets


class NumberWidget(EditorWidget):
    widgettype = 'Number'
    def __init__(self, *args, **kwargs):
        super(NumberWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return QDoubleSpinBox(parent)

    def initWidget(self, widget):
        widget.valueChanged.connect(self.validate)

    def validate(self, *args):
        self.raisevalidationupdate(passed=True)

    def updatefromconfig(self):
        config = self.config
        max = config.get('max', '')
        min = config.get('min', '')
        prefix = config.get('prefix', '')
        suffix = config.get('suffix', '')

        try:
            max = float(max)
        except ValueError:
            max = None

        try:
            min = float(min)
        except ValueError:
            min = None

        if min and max:
            self.widget.setRange(min, max)
        elif max:
            self.widget.setMaximum(max)
        elif min:
            self.widget.setMinimum(min)

        self.widget.setPrefix(prefix)
        self.widget.setSuffix(suffix)

    def setvalue(self, value):
        if not value:
            value = 0.00

        value = float(value)
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()

registerwidgets(NumberWidget)
