__ver_major__ = 2
__ver_minor__ = 0
__ver_patch__ = 2
__ver_tuple__ = (__ver_major__,__ver_minor__,__ver_patch__)
__version__ = "%d.%d.%d" % __ver_tuple__

import sip

try:
    apis = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
    for api in apis:
        sip.setapi(api, 2)
except ValueError:
    # API has already been set so we can't set it again.
    pass
