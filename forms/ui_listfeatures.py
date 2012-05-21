# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms/ui_listfeatures.ui'
#
# Created: Mon May 21 16:53:49 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ListFeatueForm(object):
    def setupUi(self, ListFeatueForm):
        ListFeatueForm.setObjectName(_fromUtf8("ListFeatueForm"))
        ListFeatueForm.setWindowModality(QtCore.Qt.NonModal)
        ListFeatueForm.resize(376, 404)
        ListFeatueForm.setWindowOpacity(1.0)
        self.gridLayout = QtGui.QGridLayout(ListFeatueForm)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.featureList = QtGui.QListWidget(ListFeatueForm)
        self.featureList.setStyleSheet(_fromUtf8("font: 14pt \"MS Shell Dlg 2\";"))
        self.featureList.setLayoutMode(QtGui.QListView.SinglePass)
        self.featureList.setObjectName(_fromUtf8("featureList"))
        self.gridLayout.addWidget(self.featureList, 1, 0, 1, 1)
        self.label = QtGui.QLabel(ListFeatueForm)
        self.label.setScaledContents(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.retranslateUi(ListFeatueForm)
        QtCore.QMetaObject.connectSlotsByName(ListFeatueForm)

    def retranslateUi(self, ListFeatueForm):
        ListFeatueForm.setWindowTitle(QtGui.QApplication.translate("ListFeatueForm", "Select form to open", None, QtGui.QApplication.UnicodeUTF8))
        self.featureList.setSortingEnabled(False)
        self.label.setText(QtGui.QApplication.translate("ListFeatueForm", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:16pt; font-weight:600;\">Select form</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))

