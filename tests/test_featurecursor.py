import pytest

from roam.infodock import FeatureCursor

@pytest.fixture
def cursor():
    features = ['One', 'Two']
    return FeatureCursor(layer=None, features=features)

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
    assert cursor.feature == 'One'
    cursor.next()
    assert cursor.feature == 'Two'

def test_should_return_no_feature_with_invalid_index(cursor):
    cursor.index = 99
    assert cursor.feature is None
