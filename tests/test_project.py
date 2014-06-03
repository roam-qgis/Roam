import pytest

from roam.project import checkversion

import roam

minversion = '2.0.2'

class TestVersionCheck:
    def test_should_return_invalid_for_version_less_then_min(self):
        projectversion = '1.0.0'
        assert checkversion(minversion, projectversion) is False

    def test_should_return_valid_for_version_higher_then_min(self):
        projectversion = '2.1.0'
        assert checkversion(minversion, projectversion)

    def test_should_return_valid_for_version_equal_to_min(self):
        minversion = '2.0.0'
        projectversion = '2.0.0'
        assert checkversion(minversion, projectversion)

    def test_should_handle_two_part_versions(self):
        projectversion = '2.0'
        assert checkversion(minversion, projectversion)

    def test_should_return_valid_same_major_version(self):
        projectversion = '2.0'
        assert checkversion(minversion, projectversion)

    def test_should_return_valid_same_patch_version(self):
        projectversion = '2.0.0'
        assert checkversion(minversion, projectversion)
