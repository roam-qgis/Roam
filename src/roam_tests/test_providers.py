import os
import pytest
from qgis.core import QgsProviderRegistry

@pytest.mark.skipif(os.name != 'nt', reason="Only on windows for now")
def test_has_ecw_support():
    filters = QgsProviderRegistry.instance().fileRasterFilters()
    # Skip if ECW not available (optional GDAL plugin)
    if 'ecw' not in filters:
        pytest.skip("ECW support not available in this QGIS build")
    assert 'ecw' in filters
