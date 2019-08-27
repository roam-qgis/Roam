import os
import pytest
import sys

# Add parent directory to path to make test aware of other modules
srcfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if srcfolder not in sys.path:
    sys.path.insert(0, srcfolder)

import roam.environ

print(sys.argv)
config = {}
roamapp = roam.environ._setup(os.getcwd(), config=config)


def tear_down():
    roamapp.exit()

@pytest.fixture(scope="session", autouse=True)
def set_up(request):
    request.addfinalizer(tear_down)
