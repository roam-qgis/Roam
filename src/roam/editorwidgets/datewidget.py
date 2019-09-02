from qgis.PyQt.QtCore import QDateTime, Qt, QSize, QDate, QEvent
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QPushButton, QDateTimeEdit, QDateEdit, QWidget
from qgis.core import NULL

from roam.api import RoamEvents
from roam.datatimerpickerwidget import DateTimePickerWidget
from roam.editorwidgets.core import EditorWidget, LargeEditorWidget
from roam.editorwidgets.uifiles import ui_datewidget


class BigDateWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(BigDateWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return DateTimePickerWidget(parent)

    def initWidget(self, widget, config):
        widget.ok.connect(self.emit_finished)
        widget.cancel.connect(self.emit_cancel)

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

    def __init__(self, *args, **kwargs):
        super(DateWidget, self).__init__(*args)
        self._is_valid = False

    def createWidget(self, parent):
        return DateUiWidget(parent)

    def initWidget(self, widget, config):
        pickbutton = widget.findChild(QPushButton)

        if not pickbutton is None:
            pickbutton.setIcon(QIcon(":/icons/calender"))
            pickbutton.setText("Select")
            pickbutton.setIconSize(QSize(24, 24))
            pickbutton.pressed.connect(self.showpickdialog)
            self.datewidget.hide()

        if type(self.datewidget) is QDateEdit:
            self.datawidget.dateChanged.connect(self.emitvaluechanged)
        else:
            self.datewidget.dateTimeChanged.connect(self.emitvaluechanged)
        self.datewidget.installEventFilter(self)

    def eventFilter(self, object, event):
        # Hack I really don't like this but there doesn't seem to be a better way at the
        # moment
        if event.type() in [QEvent.FocusIn, QEvent.MouseButtonPress]:
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

    def set_date(self, value):
        string = value.toString(Qt.SystemLocaleShortDate)
        pickbutton = self.widget.findChild(QPushButton)
        if pickbutton:
            if not string:
                string = "Select"
            pickbutton.setText(string)

    def setvalue(self, value):
        strvalue = value
        if value in [None, "", NULL]:
            value = DateWidget.DEFAULTDATE
            self._is_valid = value.isValid()
        elif isinstance(value, str):
            value = QDateTime.fromString(strvalue, Qt.ISODate)
            if not value or (value and value.date().year() < 0):
                value = QDateTime.fromString(strvalue, Qt.SystemLocaleShortDate)

            self._is_valid = value.isValid()
            if not self._is_valid:
                raise ValueError("Unable to parse date string {}".format(strvalue))

        if isinstance(value, QDate):
            value = QDateTime(value)
            self._is_valid = value.isValid()

        if hasattr(self.datewidget, 'setDate'):
            self.datewidget.setDate(value.date())

        if hasattr(self.datewidget, 'setTime'):
            self.datewidget.setTime(value.time())

        self.set_date(value)

    def value(self):
        datetime = self.datewidget.dateTime()
        if datetime == DateWidget.DEFAULTDATE:
            return None
        else:
            return datetime.toString(Qt.ISODate)
