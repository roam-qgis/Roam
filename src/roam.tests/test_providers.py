import os
import pytest
from qgis.core import QgsProviderRegistry

@pytest.mark.skipif(os.name != 'nt',
                    reason="Only on windows for now")
def test_has_ecw_support():
    assert 'ecw' in QgsProviderRegistry.instance().fileRasterFilters()
