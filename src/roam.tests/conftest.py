import os
import pytest
import sys
import roam.environ

print(sys.argv)
config = {}
roamapp = roam.environ._setup(os.getcwd(), config=config)

def tear_down():
    roamapp.exit()

@pytest.fixture(scope="session", autouse=True)
def set_up(request):
    request.addfinalizer(tear_down)
