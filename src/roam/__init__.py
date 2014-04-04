__ver_major__ = 2
__ver_minor__ = 1
__ver_patch__ = 0
__ver_tuple__ = (__ver_major__,__ver_minor__,__ver_patch__)
__version__ = "%d.%d.%d" % __ver_tuple__

import sip
import os
import sys

try:
    apis = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
    for api in apis:
        sip.setapi(api, 2)
except ValueError:
    # API has already been set so we can't set it again.
    pass


import roam.api.featureform
# Fake this module to maintain API.
sys.modules['roam.featureform'] = roam.api.featureform

curpath = os.path.dirname(__file__)

sys.path.append(curpath)
