import pytest
import roam.environ
import sys

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QApplication
import PyQt4.QtGui

roamapp = roam.environ.setup(sys.argv)

def tear_down():
    roamapp.exit()

@pytest.fixture(scope="session", autouse=True)
def set_up(request):
    request.addfinalizer(tear_down)
