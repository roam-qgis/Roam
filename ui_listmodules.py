# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_listmodules.ui'
#
# Created: Wed Apr 11 15:57:49 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ListModules(object):
    def setupUi(self, ListModules):
        ListModules.setObjectName(_fromUtf8("ListModules"))
        ListModules.setWindowModality(QtCore.Qt.NonModal)
        ListModules.resize(376, 404)
        ListModules.setWindowOpacity(1.0)
        self.gridLayout = QtGui.QGridLayout(ListModules)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.moduleList = QtGui.QListWidget(ListModules)
        self.moduleList.setStyleSheet(_fromUtf8("font: 14pt \"MS Shell Dlg 2\";"))
        self.moduleList.setLayoutMode(QtGui.QListView.SinglePass)
        self.moduleList.setObjectName(_fromUtf8("moduleList"))
        self.gridLayout.addWidget(self.moduleList, 1, 0, 1, 1)
        self.label = QtGui.QLabel(ListModules)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.retranslateUi(ListModules)
        QtCore.QMetaObject.connectSlotsByName(ListModules)

    def retranslateUi(self, ListModules):
        ListModules.setWindowTitle(QtGui.QApplication.translate("ListModules", "Select form to open", None, QtGui.QApplication.UnicodeUTF8))
        self.moduleList.setSortingEnabled(False)
        self.label.setText(QtGui.QApplication.translate("ListModules", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:16pt; font-weight:600;\">Select project to load</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))

