# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_waterForm.ui'
#
# Created: Tue Mar 27 12:19:02 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_WaterForm(object):
    def setupUi(self, WaterForm):
        WaterForm.setObjectName(_fromUtf8("WaterForm"))
        WaterForm.resize(469, 359)
        self.formLayout = QtGui.QFormLayout(WaterForm)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.descriptionLabel = QtGui.QLabel(WaterForm)
        self.descriptionLabel.setObjectName(_fromUtf8("descriptionLabel"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.descriptionLabel)
        self.MeterNo = QtGui.QLineEdit(WaterForm)
        self.MeterNo.setObjectName(_fromUtf8("MeterNo"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.MeterNo)
        self.buttonBox = QtGui.QDialogButtonBox(WaterForm)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.buttonBox)
        self.jobNoLabel = QtGui.QLabel(WaterForm)
        self.jobNoLabel.setObjectName(_fromUtf8("jobNoLabel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.jobNoLabel)
        self.jobno = QtGui.QLineEdit(WaterForm)
        self.jobno.setObjectName(_fromUtf8("jobno"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.jobno)
        self.Enabled = QtGui.QCheckBox(WaterForm)
        self.Enabled.setObjectName(_fromUtf8("Enabled"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.Enabled)
        self.AssetStatus = QtGui.QComboBox(WaterForm)
        self.AssetStatus.setFrame(True)
        self.AssetStatus.setObjectName(_fromUtf8("AssetStatus"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.AssetStatus)
        self.DateRecorded = QtGui.QCalendarWidget(WaterForm)
        self.DateRecorded.setObjectName(_fromUtf8("DateRecorded"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.DateRecorded)

        self.retranslateUi(WaterForm)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), WaterForm.reject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), WaterForm.accept)
        QtCore.QMetaObject.connectSlotsByName(WaterForm)

    def retranslateUi(self, WaterForm):
        WaterForm.setWindowTitle(QtGui.QApplication.translate("WaterForm", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.descriptionLabel.setText(QtGui.QApplication.translate("WaterForm", "Description", None, QtGui.QApplication.UnicodeUTF8))
        self.jobNoLabel.setText(QtGui.QApplication.translate("WaterForm", "Job No.", None, QtGui.QApplication.UnicodeUTF8))
        self.Enabled.setText(QtGui.QApplication.translate("WaterForm", "Enabled", None, QtGui.QApplication.UnicodeUTF8))

