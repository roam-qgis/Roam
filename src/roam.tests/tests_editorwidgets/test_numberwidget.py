import pytest
import objects

from PyQt4.QtCore import QVariant

from roam.editorwidgets.numberwidget import NumberWidget, DoubleNumberWidget, Stepper

config =  {
    "prefix": "test_pre",
    "suffix": "test_suf",
    "max": 100,
    "min": 0
}

def test_should_return_same_value():
    widget = widget=NumberWidget().createWidget(None)
    wrapper = NumberWidget(widget=widget)
    wrapper.setvalue(1)
    assert wrapper.value() == 1
    wrapper.setvalue(None)
    assert wrapper.value() == 0

def test_non_int_should_error():
    widget = widget=NumberWidget().createWidget(None)
    wrapper = NumberWidget(widget=widget)
    with pytest.raises(ValueError):
        wrapper.setvalue("Test")

def test_should_return_value_within_range():
    widget = widget=NumberWidget().createWidget(None)
    wrapper = NumberWidget(widget)
    wrapper.initWidget(widget, {})
    wrapper.config = config
    wrapper.setvalue(101)
    assert wrapper.value() == 100
    wrapper.setvalue(-1)
    assert wrapper.value() == 0
    wrapper.setvalue(1)
    assert wrapper.value() == 1

def test_sets_prfeix_suffix_on_widget():
    widget = widget=NumberWidget().createWidget(None)
    wrapper = NumberWidget(widget)
    wrapper.initWidget(widget, {})
    wrapper.config = config
    assert widget.prefix == config['prefix']
    assert widget.suffix == config['suffix']

def test_should_return_same_value_doublewidget():
    widget = widget=DoubleNumberWidget().createWidget(None)
    wrapper = NumberWidget(widget=widget)
    wrapper.setvalue(1)
    assert wrapper.value() == 1
    wrapper.setvalue(None)
    assert wrapper.value() == 0

def test_non_int_should_error():
    widget = widget=NumberWidget().createWidget(None)
    wrapper = NumberWidget(widget=widget)
    with pytest.raises(ValueError):
        wrapper.setvalue("Test")

def test_should_return_value_within_range():
    widget = widget=NumberWidget().createWidget(None)
    wrapper = NumberWidget(widget)
    wrapper.initWidget(widget, {})
    wrapper.config = config
    wrapper.setvalue(101)
    assert wrapper.value() == 100
    wrapper.setvalue(-1)
    assert wrapper.value() == 0
    wrapper.setvalue(1)
    assert wrapper.value() == 1

def test_sets_prfeix_suffix_on_widget():
    widget = widget=NumberWidget().createWidget(None)
    wrapper = NumberWidget(widget)
    wrapper.initWidget(widget, {})
    wrapper.config = config
    assert widget.prefix == config['prefix']
    assert widget.suffix == config['suffix']
