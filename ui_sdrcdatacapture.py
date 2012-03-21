# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_sdrcdatacapture.ui'
#
# Created: Wed Mar 21 16:59:57 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_SDRCDataCapture(object):
    def setupUi(self, SDRCDataCapture):
        SDRCDataCapture.setObjectName(_fromUtf8("SDRCDataCapture"))
        SDRCDataCapture.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(SDRCDataCapture)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(SDRCDataCapture)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SDRCDataCapture.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SDRCDataCapture.reject)
        QtCore.QMetaObject.connectSlotsByName(SDRCDataCapture)

    def retranslateUi(self, SDRCDataCapture):
        SDRCDataCapture.setWindowTitle(QtGui.QApplication.translate("SDRCDataCapture", "SDRCDataCapture", None, QtGui.QApplication.UnicodeUTF8))

