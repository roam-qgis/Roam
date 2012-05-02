# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'syncing\ui_sync.ui'
#
# Created: Wed May 02 14:39:48 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_syncForm(object):
    def setupUi(self, syncForm):
        syncForm.setObjectName(_fromUtf8("syncForm"))
        syncForm.resize(549, 246)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(syncForm.sizePolicy().hasHeightForWidth())
        syncForm.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(syncForm)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(syncForm)
        self.label.setMaximumSize(QtCore.QSize(200, 200))
        self.label.setText(_fromUtf8(""))
        self.label.setPixmap(QtGui.QPixmap(_fromUtf8(":/syncing/syncing/sync.png")))
        self.label.setScaledContents(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 2, 1)
        self.statusLabel = QtGui.QLabel(syncForm)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setWeight(75)
        font.setBold(True)
        self.statusLabel.setFont(font)
        self.statusLabel.setStyleSheet(_fromUtf8(""))
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setObjectName(_fromUtf8("statusLabel"))
        self.gridLayout.addWidget(self.statusLabel, 0, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(syncForm)
        font = QtGui.QFont()
        font.setPointSize(19)
        font.setWeight(50)
        font.setBold(False)
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 1, 1, 1)

        self.retranslateUi(syncForm)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), syncForm.close)
        QtCore.QMetaObject.connectSlotsByName(syncForm)

    def retranslateUi(self, syncForm):
        syncForm.setWindowTitle(QtGui.QApplication.translate("syncForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.statusLabel.setText(QtGui.QApplication.translate("syncForm", "Syncing with server\n"
"Please wait", None, QtGui.QApplication.UnicodeUTF8))
