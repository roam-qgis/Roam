import sys
import os
import nose
from PyQt4.QtGui import QApplication

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pardir)
app = QApplication(sys.argv)

def run(*args, **kwargs):
    return nose.run()