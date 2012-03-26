# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_listfeatures.ui'
#
# Created: Mon Mar 26 15:08:09 2012
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
        ListFeatueForm.resize(376, 404)
        self.gridLayout = QtGui.QGridLayout(ListFeatueForm)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.featureList = QtGui.QListWidget(ListFeatueForm)
        self.featureList.setStyleSheet(_fromUtf8("font: 14pt \"MS Shell Dlg 2\";"))
        self.featureList.setLayoutMode(QtGui.QListView.SinglePass)
        self.featureList.setObjectName(_fromUtf8("featureList"))
        self.gridLayout.addWidget(self.featureList, 0, 0, 1, 1)

        self.retranslateUi(ListFeatueForm)
        QtCore.QMetaObject.connectSlotsByName(ListFeatueForm)

    def retranslateUi(self, ListFeatueForm):
        ListFeatueForm.setWindowTitle(QtGui.QApplication.translate("ListFeatueForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.featureList.setSortingEnabled(False)

