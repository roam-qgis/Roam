import sys
from PyQt4.QtCore import QEvent
from PyQt4.QtGui import QDoubleSpinBox, QSpinBox, QWidget
import functools

from roam.api import RoamEvents
from roam.editorwidgets.core import EditorWidget, registerwidgets
from roam.editorwidgets.uifiles.ui_singlestepper import Ui_stepper

class Stepper(Ui_stepper, QWidget):
    def __init__(self, parent=None, Type=QSpinBox):
        super(Stepper, self).__init__(parent)
        self.setupUi(self)
        self.spinBox = Type()
        self.spinBox.setButtonSymbols(2)
        self.layout().insertWidget(0, self.spinBox)
        self.stepUp.pressed.connect(self.spinBox.stepUp)
        self.stepDown.pressed.connect(self.spinBox.stepDown)
        self.setRange = self.spinBox.setRange
        self.setPrefix = self.spinBox.setPrefix
        self.setSuffix = self.spinBox.setSuffix
        self.valueChanged = self.spinBox.valueChanged
        self.value = self.spinBox.value
        self.setValue = self.spinBox.setValue

    def installEventFilter(self, object):
        self.spinBox.installEventFilter(object)

class NumberWidget(EditorWidget):
    widgettype = 'Number'
    def __init__(self, *args, **kwargs):
        super(NumberWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return Stepper(parent, Type=QSpinBox)

    def initWidget(self, widget):
        widget.valueChanged.connect(self.emitvaluechanged)
        widget.installEventFilter(self)

    def eventFilter(self, object, event):
        # Hack I really don't like this but there doesn't seem to be a better way at the
        # moment
        if event.type() == QEvent.FocusIn:
            RoamEvents.openkeyboard.emit()
        return False

    def validate(self, *args):
        return True

    def updatefromconfig(self):
        config = self.config
        prefix = config.get('prefix', '')
        suffix = config.get('suffix', '')
        max, min = self._getmaxmin(config)
        self._setwidgetvalues(min, max, prefix, suffix)

    def _getmaxmin(self, config):
        max = config.get('max', '')
        min = config.get('min', '')
        try:
            max = int(max)
        except ValueError:
            max = sys.maxint

        try:
            min = int(min)
        except ValueError:
            min = -sys.maxint - 1
        return max, min

    def _setwidgetvalues(self, min, max, prefix, suffix):
        self.widget.setRange(min, max)
        self.widget.setPrefix(prefix)
        self.widget.setSuffix(suffix)

    def setvalue(self, value):
        if not value:
            value = 0

        value = int(value)
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()


class DoubleNumberWidget(NumberWidget):
    widgettype = 'Number(Double)'
    def __init__(self, *args, **kwargs):
        super(DoubleNumberWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return Stepper(parent, Type=QDoubleSpinBox)

    def initWidget(self, widget):
        super(DoubleNumberWidget, self).initWidget(widget)

    def _getmaxmin(self, config):
        max = config.get('max', '')
        min = config.get('min', '')
        try:
            max = float(max)
        except ValueError:
            max = sys.float_info.max

        try:
            min = float(min)
        except ValueError:
            min = sys.float_info.min
        print max, min
        return max, min

    def setvalue(self, value):
        if not value:
            value = 0.00

        value = float(value)
        self.widget.setValue(value)

