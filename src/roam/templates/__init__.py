import os
from PyQt4.QtCore import QUrl

base = os.path.dirname(os.path.abspath(__file__))
baseurl = QUrl.fromLocalFile(base + '/')
