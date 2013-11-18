from functools import partial

from PyQt4.QtGui import QPushButton, QDateTimeEdit, QIcon, QDateEdit
from PyQt4.QtCore import QDateTime, Qt, QSize

from qmap.editorwidgets.core import WidgetFactory, EditorWidget
from qmap.editorwidgets.uifiles import create_ui
from qmap.datatimerpickerwidget import DateTimePickerDialog

widget, base = create_ui("datewidget.ui")


class DateUiWidget(widget, base):
    def __init__(self, parent=None):
        super(DateUiWidget, self).__init__(parent)
        self.setupUi(self)


class DateWidget(EditorWidget):
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

        self.datewidget.dateTimeChanged.connect(self.validate)

    @property
    def datewidget(self):
        return self.widget.findChild(QDateTimeEdit)

    def validate(self, *args):
        if self.value() is None:
            self.raisevalidationupdate(False)
        else:
            self.raisevalidationupdate(True)

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
        if not isinstance(value, QDateTime):
            value = QDateTime.fromString(value, Qt.ISODate)

        if hasattr(self.datewidget, 'setDate'):
            self.datewidget.setDate(value.date())

        if hasattr(self.datewidget, 'setTime'):
            self.datewidget.setTime(value.time())

    def value(self):
        if self.datewidget.dateTime() == DateWidget.DEFAULTDATE:
            return None
        else:
            self.datewidget.dateTime().toString(Qt.ISODate)

factory = WidgetFactory("Date", DateWidget, None)
