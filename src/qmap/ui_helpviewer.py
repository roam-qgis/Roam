# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\nathan.woodrow\dev\qmap\qmap-admin\..\src\qmap\ui_helpviewer.ui'
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

class Ui_HelpViewer(object):
    def setupUi(self, HelpViewer):
        HelpViewer.setObjectName(_fromUtf8("HelpViewer"))
        HelpViewer.resize(489, 386)
        self.gridLayout = QtGui.QGridLayout(HelpViewer)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.webView = QtWebKit.QWebView(HelpViewer)
        self.webView.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView.setObjectName(_fromUtf8("webView"))
        self.gridLayout.addWidget(self.webView, 0, 0, 2, 2)
        self.pushButton = QtGui.QPushButton(HelpViewer)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(20)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 2)

        self.retranslateUi(HelpViewer)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("pressed()")), HelpViewer.reject)
        QtCore.QMetaObject.connectSlotsByName(HelpViewer)

    def retranslateUi(self, HelpViewer):
        HelpViewer.setWindowTitle(QtGui.QApplication.translate("HelpViewer", "Help Viewer", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("HelpViewer", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit
