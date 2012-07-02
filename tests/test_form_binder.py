#! /usr/bin/python

__author__="WOODROWN"
__date__ ="$28/06/2012 8:17:17 AM$"

import os
import unittest
import sys
from unittest import TestCase
from PyQt4.QtGui import *
from PyQt4.QtCore import *

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pardir)

from form_binder import MandatoryGroup

class testMandatoryGroups(TestCase):
    def setUp(self):
        pass
    
    def test_widgets_are_added_to_widget_list(self):
        w = QWidget()
        group = MandatoryGroup()
        group.addWidget(w)
        assert w in group.widgets

    def test_pass_if_lineedit_empty(self):
        self.called = False
        def enable():
            self.called = True

        w = QLineEdit()
        group = MandatoryGroup()
        group.addWidget(w)
        group.enable.connect( enable )
        w.setText("1")
        assert self.called == True


    def test_pass_if_textedit_empty(self):
        self.called = False
        def enable():
            self.called = True

        w = QTextEdit()
        group = MandatoryGroup()
        group.addWidget(w)
        group.enable.connect( enable )
        w.setText("1")
        assert self.called == True

    def test_pass_if_checkbox_changed(self):
        self.called = False
        def enable():
            self.called = True

        w = QCheckBox()
        group = MandatoryGroup()
        group.addWidget(w)
        group.enable.connect( enable )
        w.setCheckState(Qt.Checked)
        assert self.called == True


    def test_pass_if_combobox_changed(self):
        self.called = False
        def enable():
            self.called = True

        w = QComboBox()
        w.addItems(["1","2","3"])
        w.setCurrentIndex(1)
        group = MandatoryGroup()
        group.addWidget(w)
        group.enable.connect( enable )
        w.setCurrentIndex(2)
        assert self.called == True

    def test_pass_if_datetimedit_changed(self):
        self.called = False
        def enable():
            self.called = True

        w = QDateTimeEdit()
        group = MandatoryGroup()
        group.addWidget(w)
        group.enable.connect( enable )
        w.setDateTime(QDateTime.fromString("2012-07-02", Qt.ISODate ))
        assert self.called == True

    def test_dont_emit_signal_on_any_fail(self):
        self.called = False
        def enable():
            self.called = True

        w = QDateTimeEdit()
        w2 = QComboBox()
        w2.addItems(["","2","3"])
        w2.setCurrentIndex(0)
        group = MandatoryGroup()
        group.addWidget(w)
        group.addWidget(w2)
        group.enable.connect( enable )
        #Only change the date but not the combo box
        w.setDateTime(QDateTime.fromString("2012-07-02", Qt.ISODate ))
        assert self.called == False

    def test_emit_signal_on_all_pass(self):
        self.called = False
        def enable():
            self.called = True

        w = QDateTimeEdit()
        w2 = QComboBox()
        w2.addItems(["","2","3"])
        w2.setCurrentIndex(0)
        group = MandatoryGroup()
        group.addWidget(w)
        group.addWidget(w2)
        group.enable.connect( enable )
        #Only change the date but not the combo box
        w.setDateTime(QDateTime.fromString("2012-07-02", Qt.ISODate ))
        w2.setCurrentIndex(1)
        assert self.called == True

    def test_reports_all_widgets_left_unchanged(self):
        w = QDateTimeEdit()
        w2 = QComboBox()
        w2.addItems(["","2","3"])
        w2.setCurrentIndex(0)
        group = MandatoryGroup()
        group.addWidget(w)
        group.addWidget(w2)
        w2.setCurrentIndex(1)
        assert w in group.unchanged()
        assert not w2 in group.unchanged()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    unittest.main()
