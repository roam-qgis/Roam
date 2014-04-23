import pytest

from PyQt4.QtGui import QCheckBox

from roam.editorwidgets.checkboxwidget import CheckboxWidget

config = {"checkedvalue":'MyTrue',
          "uncheckedvalue": 'MyFalse'}

def test_should_set_config_checkedvalue_on_true():
    checkbox = QCheckBox()
    assert not checkbox.isChecked()
    widget = CheckboxWidget(widget=checkbox)
    widget.config = config
    widget.setvalue('MyTrue')
    assert checkbox.isChecked()

def test_should_set_config_uncheckedvalue_on_false():
    checkbox = QCheckBox()
    checkbox.setChecked(True)
    assert checkbox.isChecked()
    widget = CheckboxWidget(widget=checkbox)
    widget.config = config
    widget.setvalue('MyFalse')
    assert not checkbox.isChecked()

def test_should_return_uncheckedvalue_on_false():
    checkbox = QCheckBox()
    widget = CheckboxWidget(widget=checkbox)
    widget.config = config
    widget.setvalue('MyFalse')
    assert checkbox.isChecked() == False
    assert widget.value() == 'MyFalse'

