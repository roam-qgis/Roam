# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/syncing/ui_sync.ui'
#
# Created: Fri Dec 07 12:02:44 2012
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
        syncForm.resize(821, 477)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(syncForm.sizePolicy().hasHeightForWidth())
        syncForm.setSizePolicy(sizePolicy)
        syncForm.setStyleSheet(_fromUtf8("QPushButton { font: 75 20pt \"Tahoma\"; }\n"
"\n"
""))
        self.gridLayout = QtGui.QGridLayout(syncForm)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
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
        self.statusLabel = QtGui.QLabel(syncForm)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(23)
        self.statusLabel.setFont(font)
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLabel.setObjectName(_fromUtf8("statusLabel"))
        self.gridLayout.addWidget(self.statusLabel, 2, 1, 2, 2)
        self.label = QtGui.QLabel(syncForm)
        self.label.setMaximumSize(QtCore.QSize(200, 200))
        self.label.setText(_fromUtf8(""))
        self.label.setPixmap(QtGui.QPixmap(_fromUtf8(":/syncing/sync")))
        self.label.setScaledContents(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 4, 1)
        self.updatestatus = QtGui.QTextEdit(syncForm)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(20)
        font.setWeight(50)
        font.setBold(False)
        self.updatestatus.setFont(font)
        self.updatestatus.setStyleSheet(_fromUtf8("background-color: rgba(255, 255, 255, 0);"))
        self.updatestatus.setFrameShape(QtGui.QFrame.NoFrame)
        self.updatestatus.setDocumentTitle(_fromUtf8(""))
        self.updatestatus.setReadOnly(True)
        self.updatestatus.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
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
        self.updatestatus.setHtml(QtGui.QApplication.translate("syncForm", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Tahoma\'; font-size:20pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:12pt;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
import resources_rc
