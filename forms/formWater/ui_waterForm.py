# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_waterForm.ui'
#
# Created: Wed Mar 21 15:20:18 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_WaterForm(object):
    def setupUi(self, WaterForm):
        WaterForm.setObjectName(_fromUtf8("WaterForm"))
        WaterForm.resize(409, 327)
        self.gridLayout = QtGui.QGridLayout(WaterForm)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(WaterForm)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.label = QtGui.QLabel(WaterForm)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.retranslateUi(WaterForm)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), WaterForm.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), WaterForm.reject)
        QtCore.QMetaObject.connectSlotsByName(WaterForm)

    def retranslateUi(self, WaterForm):
        WaterForm.setWindowTitle(QtGui.QApplication.translate("WaterForm", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("WaterForm", "Water Capture Form", None, QtGui.QApplication.UnicodeUTF8))

