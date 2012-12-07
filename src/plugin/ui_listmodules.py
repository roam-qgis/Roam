# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/ui_listmodules.ui'
#
# Created: Fri Dec 07 11:55:55 2012
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
        ListModules.resize(813, 473)
        ListModules.setWindowOpacity(1.0)
        ListModules.setAutoFillBackground(False)
        ListModules.setStyleSheet(_fromUtf8("QListWidget::item { \n"
"border: 1px solid black; \n"
"border-radius: 5px;\n"
"}"))
        self.gridLayout = QtGui.QGridLayout(ListModules)
        self.gridLayout.setMargin(3)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.moduleList = QtGui.QListWidget(ListModules)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setWeight(75)
        font.setBold(True)
        self.moduleList.setFont(font)
        self.moduleList.setStyleSheet(_fromUtf8("background-color: rgba(255, 255, 255, 0);"))
        self.moduleList.setFrameShape(QtGui.QFrame.NoFrame)
        self.moduleList.setFrameShadow(QtGui.QFrame.Plain)
        self.moduleList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.moduleList.setProperty(_fromUtf8("showDropIndicator"), False)
        self.moduleList.setAlternatingRowColors(False)
        self.moduleList.setIconSize(QtCore.QSize(200, 200))
        self.moduleList.setTextElideMode(QtCore.Qt.ElideRight)
        self.moduleList.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerItem)
        self.moduleList.setMovement(QtGui.QListView.Static)
        self.moduleList.setFlow(QtGui.QListView.LeftToRight)
        self.moduleList.setProperty(_fromUtf8("isWrapping"), True)
        self.moduleList.setResizeMode(QtGui.QListView.Fixed)
        self.moduleList.setLayoutMode(QtGui.QListView.SinglePass)
        self.moduleList.setSpacing(0)
        self.moduleList.setGridSize(QtCore.QSize(250, 250))
        self.moduleList.setViewMode(QtGui.QListView.IconMode)
        self.moduleList.setUniformItemSizes(False)
        self.moduleList.setBatchSize(39)
        self.moduleList.setWordWrap(True)
        self.moduleList.setSelectionRectVisible(False)
        self.moduleList.setObjectName(_fromUtf8("moduleList"))
        self.gridLayout.addWidget(self.moduleList, 1, 0, 1, 1)
        self.label = QtGui.QLabel(ListModules)
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
        self.pushButton = QtGui.QPushButton(ListModules)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(20)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)

        self.retranslateUi(ListModules)
        QtCore.QMetaObject.connectSlotsByName(ListModules)

    def retranslateUi(self, ListModules):
        ListModules.setWindowTitle(QtGui.QApplication.translate("ListModules", "Select form to open", None, QtGui.QApplication.UnicodeUTF8))
        self.moduleList.setSortingEnabled(False)
        self.label.setText(QtGui.QApplication.translate("ListModules", "Select project to load", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("ListModules", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

