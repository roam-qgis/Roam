import pytest

import os
import sys

from roam.project import Form

def test_should_return_label_from_config():
    form = Form('test', {"label":"TestLabel"}, None, None)
    assert form.label == "TestLabel"

def test_should_return_name_if_no_label():
    form = Form('test', {}, None, None)
    assert form.label == 'test'

def test_should_be_invaild_when_no_name_found():
    form = Form(None, {}, None, None)
    assert not form.valid
