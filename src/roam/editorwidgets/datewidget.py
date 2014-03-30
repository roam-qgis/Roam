from functools import partial

from PyQt4.QtGui import QPushButton, QDateTimeEdit, QIcon, QDateEdit, QWidget
from PyQt4.QtCore import QDateTime, Qt, QSize

from roam.editorwidgets.core import EditorWidget
from roam.editorwidgets.uifiles import ui_datewidget
from roam.datatimerpickerwidget import DateTimePickerDialog


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
            self.datawidget.dateChanged.connect(self.validate)
        else:
            self.datewidget.dateTimeChanged.connect(self.validate)

    @property
    def datewidget(self):
        if type(self.widget) is QDateTimeEdit:
            return self.widget
        else:
            return self.widget.findChild(QDateTimeEdit)

    def validate(self, *args):
        if self.value() is None:
            self.raisevalidationupdate(False)
        else:
            self.raisevalidationupdate(True)

        self.emitvaluechanged()

    def showpickdialog(self):
        """
        Open the date time picker dialog

        control - The control that will recive the user set date time.
        """

        if type(self.datewidget) is QDateEdit:
            mode = "Date"
        else:
            mode = "DateTime"

        dlg = DateTimePickerDialog(mode)
        dlg.setWindowTitle("Select a date")
        if self.datewidget.dateTime() == DateWidget.DEFAULTDATE:
            dlg.setAsNow()
        else:
            dlg.setDateTime(self.datewidget.dateTime())

        dlg.setMinValue(self.datewidget.minimumDate())
        if dlg.exec_():
            datetime = QDateTime()
            datetime.setDate(dlg.getSelectedDate())
            datetime.setTime(dlg.getSelectedTime())
            self.setvalue(datetime)

    def setvalue(self, value):
        if value is None:
            value = DateWidget.DEFAULTDATE
        elif not isinstance(value, QDateTime):
            value = QDateTime.fromString(value, Qt.ISODate)

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

