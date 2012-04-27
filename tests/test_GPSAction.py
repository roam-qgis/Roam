import unittest
import os
import sys

# Add PARENT directory to path to make test aware of other modules
pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pardir)

from GPSAction import GPSAction

class FakeGPS():
    pass

class GPSActionTest(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()