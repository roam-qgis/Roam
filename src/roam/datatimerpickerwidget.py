from PyQt4.QtGui import QWidget, QApplication, QButtonGroup
from PyQt4.QtCore import QTime, Qt, QDateTime, pyqtSignal

from roam import utils
from roam.ui.uifiles import datepicker_widget


class DateTimePickerWidget(datepicker_widget, QWidget):
    ok = pyqtSignal()
    cancel = pyqtSignal()
    """
    A custom date picker with a time and date picker
    """
    def __init__(self, parent=None, mode="DateTime"):
        super(DateTimePickerWidget, self).__init__(parent)

        self.setupUi(self)
        self.mode = mode
        self.group = QButtonGroup()
        self.group.setExclusive(True)
        self.group.addButton(self.ambutton)
        self.group.addButton(self.pmbutton)

        self.ambutton.toggled.connect(self.isDirty)
        self.pmbutton.toggled.connect(self.isDirty)
        self.datepicker.selectionChanged.connect(self.isDirty)
        self.hourpicker.itemSelectionChanged.connect(self.isDirty)
        self.minutepicker.itemSelectionChanged.connect(self.isDirty)

        self.setasnowbutton.pressed.connect(self.setAsNow)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)

        self.okButton.pressed.connect(self.ok.emit)
        self.closebutton.pressed.connect(self.cancel.emit)

    def setMinValue(self, mindate):
        self.datepicker.setMinimumDate(mindate)

    def setmode(self, mode):
        if mode == "Date":
            self.timesection.hide()
        elif mode == "Time":
            self.datepicker.hide()

    def isDirty(self, *args):
        date = self.getSelectedDate()
        time = self.getSelectedTime()
        
        datetime = QDateTime(date, time)
        
        if self.mode == "Date":
            value = datetime.toString("ddd d MMM yyyy")
        elif self.mode == "Time":
            value = datetime.toString("hh:mm ap")
        else:   
            value = datetime.toString("ddd d MMM yyyy 'at' hh:mm ap")
            
        self.label.setText("Set as: {}".format(value))

    def setDateTime(self, datetime):
        """
        Set the picker to datatime

        datetime - The QDateTime with the value to set.
        """
        self.setTime(datetime.time())
        self.setDate(datetime.date())

    def setAsNow(self):
        """
        Set the current date and time on the picker as now.
        """
        now = QDateTime.currentDateTime()
        self.setDateTime(now)

    def setTime(self, time):
        """
        Set just the time part of the picker
        """
        hour = time.hour()
        if hour > 12:
            hour = hour - 12
        if hour == 0:
            hour = hour + 12

        minute = time.minute()
        minute = int(round(minute / 5.0) * 5.0)
        amap = time.toString("AP")
        utils.log("Hour %s Minute %s" % (hour, minute))
        try:
            houritems = self.hourpicker.findItems(str(hour), Qt.MatchFixedString)
            self.hourpicker.setCurrentItem(houritems[0])
        except IndexError:
            utils.log("Can't find hour")

        try:
            minuteitems = self.minutepicker.findItems(str(minute), Qt.MatchFixedString)
            self.minutepicker.setCurrentItem(minuteitems[0])
        except IndexError:
            utils.log("Can't find minute")

        if amap == "PM":
            self.pmbutton.toggle()

    def setDate(self, date):
        """
        Set just the date part of the picker
        """
        self.datepicker.setSelectedDate(date)

    def getSelectedTime(self):
        """
        Returns the currently selected data and time
        """
        try:
            hour = self.hourpicker.currentItem().text()
        except AttributeError:
            hour = ""

        try:
            minute = self.minutepicker.currentItem().text()
        except AttributeError:
            minute = ""

        zone = self.ambutton.isChecked() and "AM" or "PM"
        return QTime.fromString("%s%s%s" % (hour, minute, zone), "hmAP")

    def getSelectedDate(self):
        """
        Returns just the date part of the picker
        """
        return self.datepicker.selectedDate()

    @property
    def value(self):
        datetime = QDateTime()
        datetime.setDate(self.getSelectedDate())
        datetime.setTime(self.getSelectedTime())
        return datetime

    @value.setter
    def value(self, value):
        if value is None:
            self.setAsNow()
            return

        if isinstance(value, basestring):
            value = QDateTime.fromString(value, Qt.ISODate)

        self.setDate(value.date())
        self.setTime(value.time())

