import os

import roam.api.utils as utils
from qgis.core import NULL
from qgis.PyQt.QtCore import QVariant

from roam_tests.objects import make_feature


def test_copy_feature_values():
    fields = [
        dict(name="test", type=QVariant.String, length=10, value="VAL1"),
        dict(name="test2", type=QVariant.Int, length=10, value=200),
        dict(name="test3", type=QVariant.Int, length=10, value=300),
    ]
    from_feature = make_feature(fields, wkt="POINT(1 2)")
    # remove the last field so we can test skipping different fields.
    del fields[2]
    to_feature = make_feature(fields, with_values=False)
    to_feature = utils.copy_feature_values(from_feature, to_feature, include_geom=True)
    assert to_feature['test'] == "VAL1"
    assert to_feature['test2'] == 200


def test_null_check():
    null = NULL
    assert utils.nullcheck(null) is None
    assert utils.nullcheck("Test") is "Test"


def test_format_values():
    fields = ['field1', 'field2']
    values = dict(field1='Hello',
                  field2='world')
    assert utils.format_values(fields, values, with_char="|") == "Hello|world"
    assert utils.format_values(fields, values, with_char=",") == "Hello,world"
    assert utils.format_values(fields, values, with_char="\n") == "Hello\nworld"

    null = NULL
    values = dict(field1=null,
                  field2='world')

    assert utils.format_values(fields, values, with_char="|") == "world"


def test_format_values_skips_missing_fields():
    fields = ['field1', 'field2', "missingfield"]

    values = dict(field1='Hello',
                  field2='world')
    assert utils.format_values(fields, values, with_char="|") == "Hello|world"
