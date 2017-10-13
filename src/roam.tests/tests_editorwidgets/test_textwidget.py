import pytest
import objects

from PyQt4.QtCore import QVariant

from roam.editorwidgets.textwidget import TextWidget, TextBlockWidget

def test_should_return_same_value():
    widget = widget=TextWidget().createWidget(None)
    wrapper = TextWidget(widget)
    wrapper.setvalue('TEST')
    assert wrapper.value() == 'TEST'

def test_should_be_invalid_if_null():
    widget = widget=TextWidget().createWidget(None)
    wrapper = TextWidget(widget)
    wrapper.setvalue(None)
    assert not wrapper.validate()
    wrapper.setvalue("")
    assert not wrapper.validate()

def test_should_be_valid_with_value():
    widget = widget=TextWidget().createWidget(None)
    wrapper = TextWidget(widget)
    wrapper.setvalue("TEST")
    assert wrapper.validate()

def test_text_should_not_allow_longer_text_then_length():
    field = objects.makefield("TestField", QVariant.String, length=4)
    layer = objects.newmemorylayer()
    widget = widget=TextWidget().createWidget(None)
    wrapper = TextWidget(widget, field=field, layer=layer)
    wrapper.initWidget(widget, {})
    wrapper.setvalue("TEST22222")
    assert wrapper.value() == 'TEST'
