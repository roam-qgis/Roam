import logging
#! /usr/bin/python

__author__='WOODROWN'
__date__ ='$28/06/2012 8:17:17 AM$'

import os
import unittest
import sys
from mock import Mock, patch, create_autospec, call
from unittest import TestCase
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from form_binder import MandatoryGroup, FormBinder, BindingError, ControlNotFound

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

class testFormBinderBinding(TestCase):

    def getCavnasWithFakeLayers(self):
        self.layer1 = Mock()
        self.layer1.name.return_value = 'layer1'
        self.layer2 = Mock()
        self.layer2.name.return_value = 'layer2'
        self.layer3 = Mock()
        self.layer3.name.return_value = 'layer3'
        self.layer4 = Mock()
        self.layer4.name.return_value = 'layer4'
        canvas = Mock()
        canvas.layers.return_value = [self.layer1,self.layer2,
                                      self.layer3, self.layer4]
        return canvas
    
    def setUp(self):
        self.parent = QWidget()
        self.parent.setLayout(QGridLayout())
        self.layer = Mock()
        self.layer.pendingFields.return_value = []
        self.canvas = self.getCavnasWithFakeLayers()
        self.binder = FormBinder(self.layer,self.parent,self.canvas,None)

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

    def test_bind_doublespin_widget(self):
        w = QDoubleSpinBox()
        value = QVariant('2.13')
        self.assertNotEqual(w.value(), 2.13)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.value(), 2.13)

    def test_fail_bind_doubledouble_widget(self):
        w = QDoubleSpinBox()
        value = QVariant('blah')
        self.assertEqual(w.value(), 0.00)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.value(), 0.00)

    def test_bind_singlespin_widget(self):
        w = QSpinBox()
        value = QVariant('2')
        self.assertNotEqual(w.value(), 2)
        self.binder.bindValueToControl(w, value)
        self.assertEqual(w.value(), 2)

    def test_fail_bind_singlespin_widget(self):
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

    @patch.object(FormBinder, 'loadDrawingTool')
    def test_bind_drawing_tool(self, mock_loadDrawingTool):
        button = QPushButton()
        button.setText("Drawing")
        self.binder.bindValueToControl(button, QVariant())
        button.click()
        self.assertTrue(mock_loadDrawingTool.called)

    def test_bindValueToControl_raises_exception_on_fail(self):
        w = QWidget()
        self.assertRaises(BindingError,
                         self.binder.bindValueToControl, w, QVariant())

    def test_getBuddy_returns_label(self):
        w = QLineEdit()
        w.setObjectName('test')
        l = QLabel()
        l.setObjectName('test_label')
        self.parent.layout().addWidget(w)
        self.parent.layout().addWidget(l)
        
        buddy = self.binder.getBuddy(w)
        self.assertEqual(buddy, l)

    def test_getBuddy_returns_widget_if_label_not_found(self):
        w = QLineEdit()
        w.setObjectName('test')
        self.parent.layout().addWidget(w)
        buddy = self.binder.getBuddy(w)
        self.assertEqual(buddy, w)
        
    def test_mandatory_fields_should_be_added_to_mandatory_group(self):
        w = QLineEdit()
        w.setObjectName("lineedit")
        w.setProperty("mandatory",True)
        self.parent.layout().addWidget(w)
        mock_feature = Mock()
        field = Mock()
        field.name.return_value = "lineedit"
        mock_feature.attributeMap.return_value = {0:QVariant('Hello')}
        self.binder.fields = [field]

        buddy = self.binder.bindFeature(mock_feature)
        self.assertTrue((w,w) in self.binder.mandatory_group.widgets)

    def test_mandatory_fields_should_be_added_to_mandatory_group_with_buddy(self):
        w = QLineEdit()
        w.setObjectName('lineedit')
        w.setProperty("mandatory",True)
        l = QLabel()
        l.setObjectName('lineedit_label')
        self.parent.layout().addWidget(w)
        self.parent.layout().addWidget(l)
        mock_feature = Mock()
        field = Mock()
        field.name.return_value = "lineedit"
        mock_feature.attributeMap.return_value = {0:QVariant('Hello')}
        self.binder.fields = [field]

        buddy = self.binder.bindFeature(mock_feature)
        self.assertTrue((w,l) in self.binder.mandatory_group.widgets)

    def test_nonmandatory_fields_should_not_be_added_to_mandatory_group(self):
        w = QLineEdit()
        w.setObjectName("lineedit")
        w.setProperty("mandatory",False)
        self.parent.layout().addWidget(w)
        mock_feature = Mock()
        field = Mock()
        field.name.return_value = "lineedit"
        mock_feature.attributeMap.return_value = {0:QVariant('Hello')}
        self.binder.fields = [field]

        buddy = self.binder.bindFeature(mock_feature)
        self.assertTrue(not (w,w) in self.binder.mandatory_group.widgets)

    def test_bindByName_binds_by_name(self):
        w = QLineEdit()
        w.setObjectName("lineedit")
        self.parent.layout().addWidget(w)
        self.binder.bindByName("lineedit", QVariant("Hello"))
        self.assertEqual(w.text(),"Hello")

    def test_bindByName_throws_error_on_no_control_found(self):
        w = QLineEdit()
        w.setObjectName("lineedit")
        self.parent.layout().addWidget(w)
        self.assertRaises(ControlNotFound, self.binder.bindByName, \
                          "balh", QVariant("Hello") )

    def test_getControl_raise_ControlNotFound_on_missing_control(self):
        self.assertRaises(ControlNotFound, self.binder.getControl, \
                          "balh")

    def test_getControl_returns_control(self):
        w = QLineEdit()
        w.setObjectName("lineedit")
        self.parent.layout().addWidget(w)
        self.assertEqual(self.binder.getControl("lineedit"), w)

    def test_getControl_returns_control_of_correct_type(self):
        w = QLabel()
        w.setObjectName("lineedit")
        self.parent.layout().addWidget(w)
        control = self.binder.getControl("lineedit",type=QLabel)
        self.assertEqual(control, w)
        self.assertTrue(type(control) is QLabel)

    def test_bindSelectButtons_enabled_if_control_with_same_name(self):
        tool = QToolButton()
        tool.setObjectName('field_mapselect')
        tool.setProperty('from_layer','layer1')
        tool.setProperty('using_column','layer1')
        l = QLineEdit()
        l.setObjectName('field')
        self.parent.layout().addWidget(tool)
        self.parent.layout().addWidget(l)
        self.binder.bindSelectButtons()
        self.assertTrue(tool.isEnabled())

    def test_bindSelectButtons_disabled_if_no_control_found(self):
        tool = QToolButton()
        tool.setObjectName('field_mapselect')
        l = QLineEdit()
        l.setObjectName('balh')
        self.parent.layout().addWidget(tool)
        self.parent.layout().addWidget(l)
        self.binder.bindSelectButtons()
        self.assertFalse(tool.isEnabled())

    def test_bindSelectButtons_disabled_if_missing_settings(self):
        """ _mapselect buttons must have following properties
         - from_layer (string)
         - using_column (string)

         Optional properties

         - message (default to 'Please select a feature in the map')
         - searchradius (default to 5)

        """
        tool = QToolButton()
        tool.setObjectName('field_mapselect')
        tool.setProperty('from_layer','')
        l = QLineEdit()
        l.setObjectName('field')
        self.parent.layout().addWidget(tool)
        self.parent.layout().addWidget(l)
        self.binder.bindSelectButtons()
        self.assertFalse(tool.isEnabled())

    def test_bindSelectButtons_enabled_if_all_settings(self):
        tool = QToolButton()
        tool.setObjectName('field_mapselect')
        tool.setProperty('from_layer','layer1')
        tool.setProperty('using_column','')
        l = QLineEdit()
        l.setObjectName('field')
        self.parent.layout().addWidget(tool)
        self.parent.layout().addWidget(l)
        self.binder.bindSelectButtons()
        self.assertTrue(tool.isEnabled())

    def test_bindSelectButtons_disabled_if_layer_not_found(self):
        tool = QToolButton()
        tool.setObjectName('field_mapselect')
        tool.setProperty('from_layer','Test')
        tool.setProperty('using_column','Test')
        l = QLineEdit()
        l.setObjectName('field')
        self.parent.layout().addWidget(tool)
        self.parent.layout().addWidget(l)
        self.binder.bindSelectButtons()
        self.assertFalse(tool.isEnabled())
        
    @patch.object(FormBinder, 'selectFeatureClicked')
    def test_map_select_tool_called_with_correct_args(self, mock_method):
        tool = QToolButton()
        tool.setObjectName('field_mapselect')
        tool.setProperty('from_layer','layer1')
        tool.setProperty('using_column','column1')
        tool.setProperty('message','test message')
        tool.setProperty('radius', 10)
        l = QLineEdit()
        l.setObjectName('field')
        self.parent.layout().addWidget(tool)
        self.parent.layout().addWidget(l)
        self.binder.bindSelectButtons()
        tool.click()
        mock_method.assert_called_with(self.layer1,'column1','test message',10,\
                                       'field')

    @patch.object(FormBinder, 'selectFeatureClicked')
    def test_map_select_tool_called_with_correct_args_defaults(self, mock_method):
        tool = QToolButton()
        tool.setObjectName('field_mapselect')
        tool.setProperty('from_layer','layer1')
        tool.setProperty('using_column','column1')
        l = QLineEdit()
        l.setObjectName('field')
        self.parent.layout().addWidget(tool)
        self.parent.layout().addWidget(l)
        self.binder.bindSelectButtons()
        tool.click()
        mock_method.assert_called_with(self.layer1,'column1', \
                                       'Please select a feature in the map', 5, \
                                       'field')

    def test_editing_combobox_adds_value_if_not_exists(self):
        w = QComboBox()
        w.addItems(['a', 'b', 'c'])
        newitem = 'Hello World'
        expected = [newitem,'a', 'b', 'c']
        self.binder.comboEdit(newitem, w)
        items = [w.itemText(i) for i in range(w.count())]
        self.assertListEqual(expected, items)

class testFormBinderUnBinding(TestCase):
    def setUp(self):
        self.layer = Mock()
        self.layer.pendingFields.return_value = []
        self.binder = FormBinder(self.layer,None,None,None)
        
    def test_unbind_lineedit(self):
        w = QLineEdit()
        w.setText("lineedit")
        self.binder.fieldtocontrol = {0:w}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        mock_feature.changeAttribute.assert_called_once_with(0, "lineedit" )

    def test_unbind_textedit(self):
        w = QTextEdit()
        w.setText("textedit")
        self.binder.fieldtocontrol = {0:w}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        mock_feature.changeAttribute.assert_called_once_with(0, "textedit" )
        
    def test_unbind_calendar(self):
        w = QCalendarWidget()
        w.setSelectedDate(QDate.fromString("2012-06-12", Qt.ISODate ))
        self.binder.fieldtocontrol = {0:w}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        mock_feature.changeAttribute.assert_called_once_with(0, "2012-06-12" )

    def test_unbind_combobox(self):
        w = QComboBox()
        w.addItems(['', 'Hello World', 'Hello', 'World'])
        w.setCurrentIndex(1)
        self.binder.fieldtocontrol = {0:w}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        mock_feature.changeAttribute.assert_called_once_with(0, "Hello World" )

    def test_unbind_doublespin(self):
        w = QDoubleSpinBox()
        w.setValue(2.12)
        self.binder.fieldtocontrol = {0:w}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        mock_feature.changeAttribute.assert_called_once_with(0, 2.12 )

    def test_unbind_singlespin(self):
        w = QSpinBox()
        w.setValue(2)
        self.binder.fieldtocontrol = {0:w}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        mock_feature.changeAttribute.assert_called_once_with(0, 2 )

    def test_unbind_datetimeedit(self):
        w = QDateTimeEdit()
        w.setDateTime(QDateTime(2012,06,12,0,1,0,0))
        self.binder.fieldtocontrol = {0:w}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        mock_feature.changeAttribute.assert_called_once_with(0, "2012-06-12T00:01:00" )

    def test_unbind_checkbox(self):
        w = QCheckBox()
        w2 = QCheckBox()
        w.setChecked(True)
        w2.setChecked(False)
        self.binder.fieldtocontrol = {0:w, 1:w2}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        calls = [call(0,1), call(1,0)]
        mock_feature.changeAttribute.assert_has_calls(calls,any_order=True)

    def test_unbind_groupbox(self):
        w = QGroupBox()
        w2 = QGroupBox()
        w.setCheckable(True)
        w2.setCheckable(True)
        w.setChecked(True)
        w2.setChecked(False)
        self.binder.fieldtocontrol = {0:w, 1:w2}
        mock_feature = Mock()
        self.binder.unbindFeature(mock_feature)
        calls = [call(0,1), call(1,0)]
        mock_feature.changeAttribute.assert_has_calls(calls,any_order=True)


if __name__ == '__main__':
    #import nose
    #nose.run()
    logger = logging.getLogger()
    logger.disable = True
    app = QApplication(sys.argv)
    unittest.main()