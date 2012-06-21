# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms/ui_listfeatures.ui'
#
# Created: Thu Jun 21 15:54:22 2012
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
        self.verticalLayout = QtGui.QVBoxLayout(ListFeatueForm)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(ListFeatueForm)
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
        self.verticalLayout.addWidget(self.label)
        self.featureList = QtGui.QListWidget(ListFeatueForm)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.featureList.setFont(font)
        self.featureList.setStyleSheet(_fromUtf8("background-color: rgba(255, 255, 255, 0);"))
        self.featureList.setFrameShape(QtGui.QFrame.NoFrame)
        self.featureList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.featureList.setProperty(_fromUtf8("showDropIndicator"), False)
        self.featureList.setResizeMode(QtGui.QListView.Adjust)
        self.featureList.setLayoutMode(QtGui.QListView.SinglePass)
        self.featureList.setSpacing(3)
        self.featureList.setWordWrap(True)
        self.featureList.setObjectName(_fromUtf8("featureList"))
        self.verticalLayout.addWidget(self.featureList)
        self.pushButton = QtGui.QPushButton(ListFeatueForm)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Tahoma"))
        font.setPointSize(20)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton)

        self.retranslateUi(ListFeatueForm)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), ListFeatueForm.close)
        QtCore.QMetaObject.connectSlotsByName(ListFeatueForm)

    def retranslateUi(self, ListFeatueForm):
        ListFeatueForm.setWindowTitle(QtGui.QApplication.translate("ListFeatueForm", "Select form to open", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ListFeatueForm", "Select asset", None, QtGui.QApplication.UnicodeUTF8))
        self.featureList.setSortingEnabled(False)
        self.pushButton.setText(QtGui.QApplication.translate("ListFeatueForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

