import pytest

from roam.project import Form

def test_should_return_label_from_config():
    form = Form({}, None, None)
    assert form.label == "TestLabel"


