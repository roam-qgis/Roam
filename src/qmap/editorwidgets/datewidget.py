from functools import partial

from PyQt4.QtGui import QPushButton, QDateTimeEdit, QIcon, QDateEdit
from PyQt4.QtCore import QDateTime, Qt, QSize

from qmap.editorwidgets.core import WidgetFactory, EditorWidget
from qmap import nullcheck
from qmap.editorwidgets.uifiles import create_ui
from qmap.datatimerpickerwidget import DateTimePickerDialog

widget, base = create_ui("datewidget.ui")

class DateUiWidget(widget, base):
    def __init__(self, parent=None):
        super(DateUiWidget, self).__init__(parent)


class DateWidget(EditorWidget):
    def __init__(self, layer, field, widget, parent=None):
        super(DateWidget, self).__init__(layer, field, widget, parent)

    def createWidget(self, parent):
        return DateUiWidget(parent)

    def initWidget(self, widget):
        pickbutton = widget.findChild(QPushButton)
        pickbutton.setIcon(QIcon(":/icons/calender"))
        pickbutton.setText("Select")
        pickbutton.setIconSize(QSize(24, 24))
        self.datewidget = widget.findChild(QDateTimeEdit)

        if pickbutton is None:
            return

        if type(self.datewidget) is QDateEdit:
            datetype = "Date"
        else:
            datetype = "DateTime"

        pickbutton.pressed.connect(partial(self.showpickdialog, datetype))

    def showpickdialog(self, mode):
        """
        Open the date time picker dialog

        control - The control that will recive the user set date time.
        """
        dlg = DateTimePickerDialog(mode)
        dlg.setWindowTitle("Select a date")
        if self.datewidget.dateTime() == QDateTime(2000, 1, 1, 00, 00, 00, 0):
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
        if self.datewidget.dateTime() == QDateTime(2000, 1, 1, 00, 00, 00, 0):
            return None
        else:
            self.datewidget.dateTime().toString(Qt.ISODate)

factory = WidgetFactory("Date", DateWidget, None)
