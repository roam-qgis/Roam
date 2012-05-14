# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_drawingpad.ui'
#
# Created: Mon May 14 15:34:47 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DrawingWindow(object):
    def setupUi(self, DrawingWindow):
        DrawingWindow.setObjectName(_fromUtf8("DrawingWindow"))
        DrawingWindow.resize(829, 608)
        DrawingWindow.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        DrawingWindow.setTabShape(QtGui.QTabWidget.Rounded)
        DrawingWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtGui.QWidget(DrawingWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        DrawingWindow.setCentralWidget(self.centralwidget)
        self.toolBar = QtGui.QToolBar(DrawingWindow)
        self.toolBar.setMovable(False)
        self.toolBar.setAllowedAreas(QtCore.Qt.NoToolBarArea)
        self.toolBar.setIconSize(QtCore.QSize(32, 32))
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        DrawingWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        DrawingWindow.insertToolBarBreak(self.toolBar)
        self.actionClearDrawing = QtGui.QAction(DrawingWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/clearimage")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionClearDrawing.setIcon(icon)
        self.actionClearDrawing.setObjectName(_fromUtf8("actionClearDrawing"))
        self.actionRedPen = QtGui.QAction(DrawingWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/redpen")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRedPen.setIcon(icon1)
        self.actionRedPen.setObjectName(_fromUtf8("actionRedPen"))
        self.actionBluePen = QtGui.QAction(DrawingWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/bluepen")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBluePen.setIcon(icon2)
        self.actionBluePen.setObjectName(_fromUtf8("actionBluePen"))
        self.actionBlackPen = QtGui.QAction(DrawingWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/blackpen")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBlackPen.setIcon(icon3)
        self.actionBlackPen.setObjectName(_fromUtf8("actionBlackPen"))
        self.actionSave = QtGui.QAction(DrawingWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/tick")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave.setIcon(icon4)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionCancel = QtGui.QAction(DrawingWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/cancel")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCancel.setIcon(icon5)
        self.actionCancel.setObjectName(_fromUtf8("actionCancel"))
        self.toolBar.addAction(self.actionClearDrawing)
        self.toolBar.addAction(self.actionRedPen)
        self.toolBar.addAction(self.actionBluePen)
        self.toolBar.addAction(self.actionBlackPen)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addAction(self.actionCancel)

        self.retranslateUi(DrawingWindow)
        QtCore.QMetaObject.connectSlotsByName(DrawingWindow)

    def retranslateUi(self, DrawingWindow):
        DrawingWindow.setWindowTitle(QtGui.QApplication.translate("DrawingWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("DrawingWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionClearDrawing.setText(QtGui.QApplication.translate("DrawingWindow", "Clear Drawing", None, QtGui.QApplication.UnicodeUTF8))
        self.actionClearDrawing.setToolTip(QtGui.QApplication.translate("DrawingWindow", "Clear the current drawing", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRedPen.setText(QtGui.QApplication.translate("DrawingWindow", "Red Pen", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRedPen.setToolTip(QtGui.QApplication.translate("DrawingWindow", "Change pen colour to red", None, QtGui.QApplication.UnicodeUTF8))
        self.actionBluePen.setText(QtGui.QApplication.translate("DrawingWindow", "Blue Pen", None, QtGui.QApplication.UnicodeUTF8))
        self.actionBluePen.setToolTip(QtGui.QApplication.translate("DrawingWindow", "Change pen colour to blue", None, QtGui.QApplication.UnicodeUTF8))
        self.actionBlackPen.setText(QtGui.QApplication.translate("DrawingWindow", "Black Pen", None, QtGui.QApplication.UnicodeUTF8))
        self.actionBlackPen.setToolTip(QtGui.QApplication.translate("DrawingWindow", "Change pen colour to black", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave.setText(QtGui.QApplication.translate("DrawingWindow", "Save", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave.setToolTip(QtGui.QApplication.translate("DrawingWindow", "Save the current image", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCancel.setText(QtGui.QApplication.translate("DrawingWindow", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCancel.setToolTip(QtGui.QApplication.translate("DrawingWindow", "Cancel the current image", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
