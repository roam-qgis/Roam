import pytest
from roam_tests import objects

from roam.infodock import FeatureCursor, NoFeature

layer = objects.newmemorylayer()
layer = objects.addfeaturestolayer(layer, 2)

features = layer.getFeatures()
featureone = next(features)
featuretwo = next(features)

@pytest.fixture
def cursor():
    return FeatureCursor(layer=layer, features=[featureone, featuretwo])

def test_should_start_at_index_0(cursor):
    assert cursor.index == 0

def test_next_should_move_index(cursor):
    cursor.next()
    assert cursor.index == 1

def test_next_should_wrap_to_start_when_on_last(cursor):
    last = len(cursor.features) - 1
    cursor.index = last
    assert cursor.index == last
    cursor.next()
    assert cursor.index == 0

def test_back_should_wrap_to_end_when_on_first(cursor):
    last = len(cursor.features) - 1
    assert cursor.index == 0
    cursor.back()
    assert cursor.index == last

def test_should_return_feature_at_index(cursor):
    assert cursor.feature.id() == featureone.id()
    cursor.next()
    assert cursor.feature.id() == featuretwo.id()

def test_should_raise_no_feature_on_invalid_index(cursor):
    cursor.index = 99
    with pytest.raises(NoFeature):
        cursor.feature
