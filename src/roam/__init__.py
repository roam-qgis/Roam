__ver_major__ = 2
__ver_minor__ = 2
__ver_patch__ = 0
__ver_tuple__ = (__ver_major__,__ver_minor__,__ver_patch__)
__version__ = "%d.%d.%d" % __ver_tuple__

import sip
import os
import sys

try:
    types = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
    for qtype in types:
        sip.setapi(qtype, 2)
except ValueError:
    # API has already been set so we can't set it again.
    pass


curpath = os.path.dirname(__file__)

sys.path.append(curpath)
