# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\dev\roam\src\configmanager\editorwidgets\uifiles\checkwidget_config.ui'
#
# Created: Fri Jan 31 13:42:23 2014
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(400, 300)
        self.formLayout = QtGui.QFormLayout(Form)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_3)
        self.checkedText = QtGui.QLineEdit(Form)
        self.checkedText.setObjectName(_fromUtf8("checkedText"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.checkedText)
        self.label_4 = QtGui.QLabel(Form)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_4)
        self.uncheckedText = QtGui.QLineEdit(Form)
        self.uncheckedText.setObjectName(_fromUtf8("uncheckedText"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.uncheckedText)
        spacerItem = QtGui.QSpacerItem(20, 104, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.formLayout.setItem(4, QtGui.QFormLayout.FieldRole, spacerItem)

        self.retranslateUi(Form)
        QtCore.QObject.connect(self.checkedText, QtCore.SIGNAL(_fromUtf8("textChanged(QString)")), Form.widgetchanged)
        QtCore.QObject.connect(self.uncheckedText, QtCore.SIGNAL(_fromUtf8("textChanged(QString)")), Form.widgetchanged)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Form", "Checked value", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Form", "Unchecked value", None, QtGui.QApplication.UnicodeUTF8))

