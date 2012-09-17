import sys
import os
from PyQt4.QtGui import QApplication

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pardir)
app = QApplication(sys.argv)

from test_form_binder import *
from test_syncer import *
