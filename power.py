#! /usr/bin/python

import win32gui
import win32con
import win32api
from PyQt4.QtGui import *
from PyQt4.QtCore import QObject, pyqtSignal
import sys

class PowerState(QObject):
    poweroff = pyqtSignal()
    poweron = pyqtSignal()
    def __init__(self, widget):
        QObject.__init__(self)
        self.widget = widget
        self.__oldProc = win32gui.SetWindowLong(self.widget.winId(), \
                                                win32con.GWL_WNDPROC,\
                                                self.__WndProc)

    def __WndProc(self, hWnd, msg, wParam, lParam):
        if msg == win32con.WM_POWERBROADCAST:
            if wParam == win32con.PBT_APMSUSPEND:
                self.poweroff.emit()
            elif wParam == win32con.PBT_APMRESUMEAUTOMATIC:
                self.poweron.emit()

        return win32gui.CallWindowProc(self.__oldProc,hWnd, msg, wParam, lParam)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wid = QWidget()
    power = PowerState(wid)
    wid.show()
    sys.exit(app.exec_())
