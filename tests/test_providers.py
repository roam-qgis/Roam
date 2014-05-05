from qgis.core import QgsProviderRegistry


def test_has_ecw_support():
    assert 'ecw' in QgsProviderRegistry.instance().fileRasterFilters()
