import pytest

from mock import patch

import os
import sys

from roam.project import Form

def test_should_return_label_from_config():
    form = Form('test', {"label":"TestLabel"}, None)
    assert form.label == "TestLabel"

def test_should_return_name_if_no_label():
    form = Form('test', {}, None)
    assert form.label == 'test'

def test_should_return_layer_name_from_config():
    form = Form('test', {'layer': 'TestLayer'}, None)
    assert form.layername == 'TestLayer'

def test_should_return_list_of_defined_widgets():
    widgetone = {'field':'test'}
    widgettwo = {'field':'test2'}
    widgets = [widgetone, widgettwo]
    config = dict(widgets=widgets)
    form = Form('test', config, None)
    assert form.widgets == widgets

def test_should_return_no_widgets_when_not_found():
    form = Form('test', {}, None)
    assert form.widgets == []
