import pytest
from PyQt5.QtCore import QDate, QTime

from PyQt5.QtWidgets import QCheckBox

from roam.editorwidgets.datewidget import DateWidget, DateUiWidget
from roam.editorwidgets.core import createwidget, widgetwrapper

config = {}

TYPE = "Date"


def test_should_set_return_none_on_none():
    qtwidget = createwidget(TYPE)
    wrapper = widgetwrapper(TYPE, qtwidget, config, layer=None, label=None, field=None)
    wrapper.setvalue(None)
    assert wrapper.value() is None


def test_invalid_date_marks_widget_as_invalid():
    qtwidget = createwidget(TYPE)
    wrapper = widgetwrapper(TYPE, qtwidget, config, layer=None, label=None, field=None)
    assert wrapper._is_valid is False
    with pytest.raises(ValueError):
        wrapper.setvalue("2008-12")
        assert wrapper._is_valid is False
        assert wrapper.validate() is False


def test_iso_date_returns_valid():
    qtwidget = createwidget(TYPE)
    wrapper = widgetwrapper(TYPE, qtwidget, config, layer=None, label=None, field=None)
    input = "2017-07-24T15:46:29"
    wrapper.setvalue(input)
    expected = "2017-07-24T15:46:29"
    assert wrapper.value() == expected
    assert wrapper.validate() is True
    input = "2017-07-24"
    wrapper.setvalue(input)
    expected = "2017-07-24T00:00:00"
    assert wrapper.value() == expected
    assert wrapper.validate() is True


def test_widget_date_returns_correctly():
    qtwidget = createwidget(TYPE)
    wrapper = widgetwrapper(TYPE, qtwidget, config, layer=None, label=None, field=None)
    assert wrapper.validate() is False
    wrapper.datewidget.setDate(QDate(2017, 07, 24))
    wrapper.datewidget.setTime(QTime(15, 46, 29))
    expected = "2017-07-24T15:46:29"
    assert wrapper.value() == expected
