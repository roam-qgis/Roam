# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\nathan.woodrow\dev\qmap\qmap-admin\..\src\qmap\ui_errorlist.ui'
#
# Created: Tue Apr 23 11:37:23 2013
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(560, 467)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(Dialog)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(23)
        font.setWeight(75)
        font.setUnderline(False)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        self.label.setMargin(5)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.errorList = QtGui.QListWidget(Dialog)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.errorList.setFont(font)
        self.errorList.setStyleSheet(_fromUtf8("background-color: rgba(255, 255, 255, 0);"))
        self.errorList.setFrameShape(QtGui.QFrame.NoFrame)
        self.errorList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.errorList.setProperty(_fromUtf8("showDropIndicator"), False)
        self.errorList.setAlternatingRowColors(False)
        self.errorList.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.errorList.setResizeMode(QtGui.QListView.Adjust)
        self.errorList.setLayoutMode(QtGui.QListView.SinglePass)
        self.errorList.setSpacing(3)
        self.errorList.setWordWrap(True)
        self.errorList.setObjectName(_fromUtf8("errorList"))
        self.gridLayout.addWidget(self.errorList, 1, 0, 1, 1)
        self.pushButton = QtGui.QPushButton(Dialog)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(20)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Please corrent the following errors", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Please correct the following errors", None, QtGui.QApplication.UnicodeUTF8))
        self.errorList.setSortingEnabled(False)
        self.pushButton.setText(QtGui.QApplication.translate("Dialog", "OK", None, QtGui.QApplication.UnicodeUTF8))

