import pytest

from roam.editorwidgets.optionwidget import OptionWidget

items = dict(items=[
    "1",
    "2"
])
config = dict(list=items)


def test_create_button_for_each_item():
    # WAT?!
    widget = OptionWidget().createWidget()
    option = OptionWidget(widget=widget)
    option.initWidget(widget, {})
    option.config = config
    assert len(option.buttons) == 2
    for button in option.buttons:
        assert button.text() in items['items']


def test_multi_returns_list():
    # WAT?!
    widget = OptionWidget().createWidget()
    option = OptionWidget(widget=widget)
    option.initWidget(widget, {})
    config['multi'] = True
    option.config = config
    option.setvalue("1;2")
    assert option.value() == "1;2"


def test_single_option_returns_single_value():
    # WAT?!
    widget = OptionWidget().createWidget()
    option = OptionWidget(widget=widget)
    option.initWidget(widget, {})
    option.config = config
    option.setvalue("1")
    assert option.value() == "1"


def test_no_value_returns_none():
    # WAT?!
    widget = OptionWidget().createWidget()
    option = OptionWidget(widget=widget)
    option.initWidget(widget, {})
    option.config = config
    assert option.value() is None


def test_no_value_returns_none_multi():
    # WAT?!
    widget = OptionWidget().createWidget()
    option = OptionWidget(widget=widget)
    option.initWidget(widget, {})
    config['multi'] = True
    option.config = config
    assert option.value() is None




