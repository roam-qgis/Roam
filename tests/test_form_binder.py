#! /usr/bin/python

__author__='WOODROWN'
__date__ ='$28/06/2012 8:17:17 AM$'

import os
import unittest
import sys
from mock import Mock, patch
from unittest import TestCase
from PyQt4.QtGui import *
from PyQt4.QtCore import *

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pardir)

from form_binder import MandatoryGroup, FormBinder

class testMandatoryGroups(TestCase):
    def setUp(self):
        pass
    
    def test_widgets_are_added_to_widget_list(self):
        w = QWidget()
        group = MandatoryGroup()
        assert not (w,w) in group.widgets, 'Widget already in group :S'
        group.addWidget(w, w)
        assert (w,w) in group.widgets, 'Widget not in group'

    def test_mandatory_flag_is_set_on_buddy_widget(self):
        w = QWidget()
        group = MandatoryGroup()
        self.assertFalse(w.property('mandatory').toBool())
        group.addWidget(w, w)
        self.assertTrue(w.property('mandatory').toBool())

    def test_ok_flag_is_set_on_buddy_widget_if_pass(self):
        w = QLineEdit()
        l = QLabel()
        group = MandatoryGroup()
        group.addWidget(w, l)
        self.assertFalse(l.property('ok').toBool())
        w.setText('1')
        self.assertTrue(l.property('ok').toBool())

    def test_ok_flag_is_set_false_on_buddy_widget_if_pass(self):
        w = QLineEdit()
        l = QLabel()
        group = MandatoryGroup()
        group.addWidget(w, l)
        self.assertFalse(l.property('ok').toBool())

    def test_stylesheet_is_set_on_buddy_widget(self):
        w = QWidget()
        l = QLabel()
        group = MandatoryGroup()
        group.addWidget(w, l)
        self.assertFalse(l.styleSheet().isEmpty())

        w = QWidget()
        l = QGroupBox()
        group = MandatoryGroup()
        group.addWidget(w, l)
        self.assertFalse(l.styleSheet().isEmpty())

        w = QWidget()
        l = QCheckBox()
        group = MandatoryGroup()
        group.addWidget(w, l)
        self.assertFalse(l.styleSheet().isEmpty())

    def test_pass_if_lineedit_empty(self):
        self.called = False
        def enable():
            self.called = True

        w = QLineEdit()
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.enable.connect( enable )
        w.setText('1')
        self.assertTrue(self.called)


    def test_pass_if_textedit_empty(self):
        self.called = False
        def enable():
            self.called = True

        w = QTextEdit()
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.enable.connect( enable )
        w.setText('1')
        self.assertTrue(self.called)

    def test_pass_if_checkbox_changed(self):
        self.called = False
        def enable():
            self.called = True

        w = QCheckBox()
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.enable.connect( enable )
        w.setCheckState(Qt.Checked)
        self.assertTrue(self.called)


    def test_pass_if_combobox_changed(self):
        self.called = False
        def enable():
            self.called = True

        w = QComboBox()
        w.addItems(['1','2','3'])
        w.setCurrentIndex(1)
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.enable.connect( enable )
        w.setCurrentIndex(2)
        self.assertTrue(self.called)

    def test_pass_if_datetimedit_changed(self):
        self.called = False
        def enable():
            self.called = True

        w = QDateTimeEdit()
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.enable.connect( enable )
        w.setDateTime(QDateTime.fromString('2012-07-02', Qt.ISODate ))
        self.assertTrue(self.called)

    def test_dont_emit_signal_on_any_fail(self):
        self.called = False
        def enable():
            self.called = True

        w = QDateTimeEdit()
        w2 = QComboBox()
        w2.addItems(['','2','3'])
        w2.setCurrentIndex(0)
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.addWidget(w2, w2)
        group.enable.connect( enable )
        #Only change the date but not the combo box
        w.setDateTime(QDateTime.fromString('2012-07-02', Qt.ISODate ))
        self.assertTrue(self.called == False)

    def test_emit_signal_on_all_pass(self):
        self.called = False
        def enable():
            self.called = True

        w = QDateTimeEdit()
        w2 = QComboBox()
        w2.addItems(['','2','3'])
        w2.setCurrentIndex(0)
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.addWidget(w2, w2)
        group.enable.connect( enable )
        w.setDateTime(QDateTime.fromString('2012-07-02', Qt.ISODate ))
        w2.setCurrentIndex(1)
        self.assertTrue(self.called)

    def test_reports_all_widgets_left_unchanged(self):
        w = QDateTimeEdit()
        w2 = QComboBox()
        w2.addItems(['','2','3'])
        w2.setCurrentIndex(0)
        group = MandatoryGroup()
        group.addWidget(w, w)
        group.addWidget(w2, w2)
        w2.setCurrentIndex(1)
        self.assertTrue(w in group.unchanged())
        self.assertFalse(w2 in group.unchanged())

class testFormBinder(TestCase):
    def setUp(self):
        self.layer = Mock()
        self.layer.pendingFields.return_value = []
        self.binder = FormBinder(self.layer,None,None,None)

    def test_bind_calender_widget(self):
        w = QCalendarWidget()
        # Set the date to something other then today which is the default
        w.setSelectedDate(QDate(2012,5,04))
        value = QVariant('2012-07-04')
        expected = QDate(2012,07,04)
        self.assertNotEqual(w.selectedDate(),expected)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.selectedDate(), expected)

    def test_bind_lineedit_widget(self):
        w = QLineEdit()
        value = QVariant('Hello World')
        expected = 'Hello World'
        self.assertNotEqual(w.text(), expected)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.text(), expected)

    def test_bind_textedit_widget(self):
        w = QTextEdit()
        value = QVariant('Hello World')
        expected = 'Hello World'
        self.assertNotEqual(w.toPlainText(), expected)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.toPlainText(), expected)

    def test_bind_checkbox_widget(self):
        values = [(1,True),
                  ('True',True),
                  ('true',True),
                  (0,False),
                  ('False',False),
                  ('false',False)]
        w = QCheckBox()
        for string, expected in values:
            value = QVariant(string)
            self.binder.bindValueToControl(w, value)
            self.assertEqual(w.isChecked(), expected)

    def test_bind_groupbox_widget(self):
        values = [(1,True),
                  ('True',True),
                  ('true',True),
                  (0,False),
                  ('False',False),
                  ('false',False)]
        w = QGroupBox()
        w.setCheckable(True)
        for string, expected in values:
            value = QVariant(string)
            self.binder.bindValueToControl(w, value)
            self.assertEqual(w.isChecked(),expected)
            
    def test_bind_handles_uncheckable_groupbox(self):
        w = QGroupBox()
        w.setCheckable(False)
        self.binder.bindValueToControl(w, QVariant(True))
        self.assertFalse(w.isChecked())

    def test_bind_combox_widget(self):
        w = QComboBox()
        w.addItems([QString('Hello World'), QString('Hello'), QString('World')])
        value = QVariant('Hello')
        self.assertNotEqual(w.currentText(), value.toString())
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.currentText(), value.toString())

    def test_fail_bind_combox_widget(self):
        w = QComboBox()
        w.addItems(['', 'Hello World', 'Hello', 'World'])
        value = QVariant('balh')
        self.assertEqual(w.currentText(), '')
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.currentText(), '')

    def test_bind_double_widget(self):
        w = QDoubleSpinBox()
        value = QVariant('2.13')
        self.assertNotEqual(w.value(), 2.13)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.value(), 2.13)

    def test_fail_bind_double_widget(self):
        w = QDoubleSpinBox()
        value = QVariant('blah')
        self.assertEqual(w.value(), 0.00)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.value(), 0.00)

    def test_bind_double_widget(self):
        w = QSpinBox()
        value = QVariant('2')
        self.assertNotEqual(w.value(), 2)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.value(), 2)

    def test_fail_bind_double_widget(self):
        w = QSpinBox()
        value = QVariant('blah')
        self.assertEqual(w.value(), 0.00)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.value(), 0.00)

    def test_bind_datetimeedit_widget(self):
        w = QDateTimeEdit()
        value = QVariant('2012-12-05T00:12:00')
        expected = QDateTime(2012,12,05,00,12,00)
        self.assertNotEqual(w.dateTime(), expected)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.dateTime(), expected)

    @patch.object(FormBinder, 'pickDateTime')
    def test_bind_datetimeedit_picker(self, mock_method):
        widget = QWidget()
        l = QGridLayout(widget)
        b = QPushButton()
        w = QDateTimeEdit()
        b.setObjectName('testdatetime_pick')
        w.setObjectName('testdatetime')
        l.addWidget(b)
        l.addWidget(w)
        self.binder.bindValueToControl(w, QVariant())
        b.click()
        self.assertTrue(mock_method.called_with(w))

    @patch.object(FormBinder, 'pickDateTime')
    def test_bind_more_then_one_datetimeedit_picker(self, mock_method):
        widget = QWidget()
        l = QGridLayout(widget)
        b = QPushButton()
        w = QDateTimeEdit()
        b.setObjectName('testdatetime_pick')
        w.setObjectName('testdatetime')
        l.addWidget(b)
        l.addWidget(w)
        widget2 = QWidget()
        l2 = QGridLayout(widget2)
        b2 = QPushButton()
        w2 = QDateTimeEdit()
        b2.setObjectName('testdatetime2_pick')
        w2.setObjectName('testdatetime2')
        l2.addWidget(b2)
        l2.addWidget(w2)
        self.binder.bindValueToControl(w, QVariant())
        self.binder.bindValueToControl(w2, QVariant())
        b.click()
        mock_method.assert_called_with(w,"DateTime")
        b2.click()
        mock_method.assert_called_with(w2,"DateTime")
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    unittest.main()
