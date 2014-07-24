from qgis.core import QgsProviderRegistry


def test_has_ecw_support():
    print "Filters", QgsProviderRegistry.instance().fileRasterFilters() == ''
    assert 'ecw' in QgsProviderRegistry.instance().fileRasterFilters()
