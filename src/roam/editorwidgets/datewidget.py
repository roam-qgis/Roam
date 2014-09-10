from functools import partial

from PyQt4.QtGui import QPushButton, QDateTimeEdit, QIcon, QDateEdit, QWidget
from PyQt4.QtCore import QDateTime, Qt, QSize, QDate, QEvent

from roam.api import RoamEvents
from roam.editorwidgets.core import EditorWidget, registerwidgets, LargeEditorWidget
from roam.editorwidgets.uifiles import ui_datewidget
from roam.datatimerpickerwidget import DateTimePickerWidget


class BigDateWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(BigDateWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return DateTimePickerWidget(parent)

    def initWidget(self, widget):
        widget.ok.connect(self.emitfished)
        widget.cancel.connect(self.emitcancel)

    def updatefromconfig(self):
        super(BigDateWidget, self).updatefromconfig()
        mode = self.config['mode']
        mindate = self.config['mindate']
        self.widget.setMinValue(mindate)
        self.widget.setmode(mode)
        self.endupdatefromconfig()

    def setvalue(self, value):
        self.widget.value = value

    def value(self):
        return self.widget.value


class DateUiWidget(ui_datewidget.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(DateUiWidget, self).__init__()
        self.setupUi(self)


class DateWidget(EditorWidget):
    widgettype = 'Date'
    DEFAULTDATE = QDateTime(2000, 1, 1, 00, 00, 00, 0)

    def __init__(self, *args):
        super(DateWidget, self).__init__(*args)

    def createWidget(self, parent):
        return DateUiWidget(parent)

    def initWidget(self, widget):
        pickbutton = widget.findChild(QPushButton)

        if not pickbutton is None:
            pickbutton.setIcon(QIcon(":/icons/calender"))
            pickbutton.setText("Select")
            pickbutton.setIconSize(QSize(24, 24))
            pickbutton.pressed.connect(self.showpickdialog)

        if type(self.datewidget) is QDateEdit:
            self.datawidget.dateChanged.connect(self.emitvaluechanged)
        else:
            self.datewidget.dateTimeChanged.connect(self.emitvaluechanged)
        self.datewidget.installEventFilter(self)

    def eventFilter(self, object, event):
        # Hack I really don't like this but there doesn't seem to be a better way at the
        # moment
        if event.type() == QEvent.FocusIn:
            RoamEvents.openkeyboard.emit()
        return False

    @property
    def datewidget(self):
        if type(self.widget) is QDateTimeEdit:
            return self.widget
        else:
            return self.widget.findChild(QDateTimeEdit)

    def validate(self, *args):
        if self.value() is None:
            return False
        else:
            return True

    def showpickdialog(self):
        """
        Open the date time picker dialog

        control - The control that will recive the user set date time.
        """

        if type(self.datewidget) is QDateEdit:
            mode = "Date"
        else:
            mode = "DateTime"

        config = dict(mode=mode,
                      mindate=self.datewidget.minimumDate())

        self.largewidgetrequest.emit(BigDateWidget, self.value(),
                                     self.setvalue, config)

    def setvalue(self, value):
        if value is None:
            value = DateWidget.DEFAULTDATE
        elif isinstance(value, basestring):
            value = QDateTime.fromString(value, Qt.ISODate)

        if isinstance(value, QDate):
            value = QDateTime(value)

        if hasattr(self.datewidget, 'setDate'):
            self.datewidget.setDate(value.date())

        if hasattr(self.datewidget, 'setTime'):
            self.datewidget.setTime(value.time())

    def value(self):
        datetime = self.datewidget.dateTime()
        if datetime == DateWidget.DEFAULTDATE:
            return None
        else:
            return datetime.toString(Qt.ISODate)
