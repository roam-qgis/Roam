import os

import roam.api.utils as utils
from PyQt4.QtCore import  QVariant

from objects import make_feature

def test_copy_feature_values():
    fields = [
        dict(name="test", type=QVariant.String, length=10, value="VAL1"),
        dict(name="test2", type=QVariant.Int, length=10, value=200),
    ]
    from_feature = make_feature(fields, wkt="POINT(1 2)")
    to_feature = make_feature(fields, with_values=False)
    to_feature = utils.copy_feature_values(from_feature, to_feature, include_geom=True)
    assert to_feature['test'] == "VAL1"
    assert to_feature['test2'] == 200

