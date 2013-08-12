from PyQt4.QtGui import QDialog,QApplication, QButtonGroup
from PyQt4.QtCore import QTime, Qt, QDateTime

import utils
from uifiles import datepicker_widget, datepicker_base


class DateTimePickerDialog(datepicker_widget, datepicker_base):
    """
    A custom date picker with a time and date picker
    """
    def __init__(self, mode="DateTime"):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
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

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.setasnowbutton.pressed.connect(self.setAsNow)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)

        if mode == "Date":
            self.timesection.hide()
            self.setasnowbutton.setText("Set as current date")
        elif mode == "Time":
            self.datepicker.hide()
            self.setasnowbutton.setText("Set as current time")

    def isDirty(self, *args):
        date = self.getSelectedDate()
        time = self.getSelectedTime()
        
        datetime = QDateTime(date, time)
        
        if self.mode == "Date":
            value = datetime.toString("ddd d MMM yyyy")
        elif self.mode == "Time":
            value = datetime.toString("h:m ap") 
        else:   
            value = datetime.toString("ddd d MMM yyyy 'at' h:m ap")
            
        self.label.setText(value)

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

if __name__ == "__main__":
    app = QApplication([])
    dlg = DateTimePickerDialog()
    dlg.show()
    app.exec_()