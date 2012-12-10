from PyQt4.QtGui import QDialog,QApplication, QButtonGroup
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
        self.group = QButtonGroup()
        self.group.setExclusive(True)
        self.group.addButton(self.ui.ambutton)
        self.group.addButton(self.ui.pmbutton)

        self.ui.ambutton.toggled.connect(self.isDirty)
        self.ui.pmbutton.toggled.connect(self.isDirty)
        self.ui.datepicker.selectionChanged.connect(self.isDirty)
        self.ui.hourpicker.itemSelectionChanged.connect(self.isDirty)
        self.ui.minutepicker.itemSelectionChanged.connect(self.isDirty)

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

    def isDirty(self, *args):
        date = self.getSelectedDate()
        time = self.getSelectedTime()
        datetime = QDateTime(date, time)
        value = datetime.toString("ddd d MMM yyyy 'at' h:m ap")
        self.ui.label.setText(value)

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
            self.ui.pmbutton.toggle()

    def setDate(self, date):
        """
        Set just the date part of the picker
        """
        self.ui.datepicker.setSelectedDate(date)

    def getSelectedTime(self):
        """
        Returns the currently selected data and time
        """
        try:
            hour = self.ui.hourpicker.currentItem().text()
        except AttributeError:
            hour = ""

        try:
            minute = self.ui.minutepicker.currentItem().text()
        except AttributeError:
            minute = ""

        zone = self.ui.ambutton.isChecked() and "AM" or "PM"
        return QTime.fromString("%s%s%s" % (hour, minute, zone), "hmAP")

    def getSelectedDate(self):
        """
        Returns just the date part of the picker
        """
        return self.ui.datepicker.selectedDate()

if __name__ == "__main__":
    app = QApplication([])
    dlg = DateTimePickerDialog()
    dlg.show()
    app.exec_()