# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\nathan.woodrow\dev\qmap\qmap-admin\..\src\qmap\syncing/ui_sync.ui'
#
# Created: Tue Apr 23 11:37:22 2013
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
        syncForm.resize(887, 421)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(syncForm.sizePolicy().hasHeightForWidth())
        syncForm.setSizePolicy(sizePolicy)
        syncForm.setStyleSheet(_fromUtf8("QPushButton { font: 75 20pt \"Tahoma\"; }\n"
"\n"
""))
        self.gridLayout = QtGui.QGridLayout(syncForm)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.header = QtGui.QLabel(syncForm)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(23)
        font.setWeight(75)
        font.setItalic(False)
        font.setBold(True)
        self.header.setFont(font)
        self.header.setStyleSheet(_fromUtf8(""))
        self.header.setAlignment(QtCore.Qt.AlignCenter)
        self.header.setWordWrap(True)
        self.header.setObjectName(_fromUtf8("header"))
        self.gridLayout.addWidget(self.header, 0, 1, 1, 2)
        self.label = QtGui.QLabel(syncForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMaximumSize(QtCore.QSize(200, 200))
        self.label.setText(_fromUtf8(""))
        self.label.setPixmap(QtGui.QPixmap(_fromUtf8(":/syncing/sync")))
        self.label.setScaledContents(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 4, 1)
        self.statusLabel = QtGui.QLabel(syncForm)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(23)
        self.statusLabel.setFont(font)
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLabel.setObjectName(_fromUtf8("statusLabel"))
        self.gridLayout.addWidget(self.statusLabel, 2, 1, 2, 2)
        self.buttonBox = QtGui.QDialogButtonBox(syncForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(23)
        font.setWeight(50)
        font.setItalic(False)
        font.setBold(False)
        self.buttonBox.setFont(font)
        self.buttonBox.setStyleSheet(_fromUtf8(""))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 6, 1, 1, 2)
        self.updatestatus = QtGui.QListWidget(syncForm)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setWeight(50)
        font.setBold(False)
        self.updatestatus.setFont(font)
        self.updatestatus.setStyleSheet(_fromUtf8("background-color: rgba(255, 255, 255, 0);"))
        self.updatestatus.setFrameShape(QtGui.QFrame.HLine)
        self.updatestatus.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.updatestatus.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.updatestatus.setLayoutMode(QtGui.QListView.SinglePass)
        self.updatestatus.setObjectName(_fromUtf8("updatestatus"))
        self.gridLayout.addWidget(self.updatestatus, 1, 1, 1, 1)

        self.retranslateUi(syncForm)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), syncForm.close)
        QtCore.QMetaObject.connectSlotsByName(syncForm)

    def retranslateUi(self, syncForm):
        syncForm.setWindowTitle(QtGui.QApplication.translate("syncForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.header.setText(QtGui.QApplication.translate("syncForm", "Sync in progress", None, QtGui.QApplication.UnicodeUTF8))
        self.statusLabel.setText(QtGui.QApplication.translate("syncForm", "Total Downloaded: - \n"
"Total Uploaded: - ", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
import resources_rc
