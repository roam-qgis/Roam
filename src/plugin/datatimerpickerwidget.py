from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QTime, Qt, QDateTime, QString
from ui_datatimerpicker import Ui_datatimerpicker
from qgis.core import *
from utils import log


class DateTimePickerDialog(QDialog):
    """
    A custom date picker with a time and date picker
    """
    def __init__(self, mode="DateTime"):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_datatimerpicker()
        self.ui.setupUi(self)
        self.ui.ampmbutton.toggled.connect(self._switchampm)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.setasnowbutton.pressed.connect(self.setAsNow)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)

        if mode == "Date":
            self.ui.hourpicker.hide()
            self.ui.minutepicker.hide()
            self.ui.ampmbutton.hide()
        elif mode == "Time":
            self.ui.datepicker.hide()

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
        log("Hour %s Minute %s" % (hour, minute))
        try:
            houritems = self.ui.hourpicker.findItems(str(hour), Qt.MatchFixedString)
            self.ui.hourpicker.setCurrentItem(houritems[0])
        except IndexError:
            log("Can't find hour")

        try:
            minuteitems = self.ui.minutepicker.findItems(str(minute), Qt.MatchFixedString)
            self.ui.minutepicker.setCurrentItem(minuteitems[0])
        except IndexError:
            log("Can't find minute")

        if amap == "PM":
            self.ui.ampmbutton.setChecked(True)

    def setDate(self, date):
        """
        Set just the date part of the picker
        """
        self.ui.datepicker.setSelectedDate(date)

    def getSelectedTime(self):
        """
        Returns the currently selected data and time
        """
        hour = self.ui.hourpicker.currentItem().text()
        minute = self.ui.minutepicker.currentItem().text()
        ampm = self.ui.ampmbutton.text()
        return QTime.fromString("%s%s%s" % (hour, minute, ampm), "hmAP")

    def getSelectedDate(self):
        """
        Returns just the date part of the picker
        """
        return self.ui.datepicker.selectedDate()

    def _switchampm(self, checked):
        text = "AM"
        if checked:
            text = "PM"
        self.ui.ampmbutton.setText(text)