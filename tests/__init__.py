
__author__="WOODROWN"
__date__ ="$21/03/2012 11:48:35 AM$"

import test_form_binder
import unittest
import sys
from PyQt4.QtGui import QApplication

def main():
    app = QApplication(sys.argv)
    suite = unittest.TestLoader().discover('.')
    results = unittest.TextTestRunner(verbosity=0).run(suite)
    return results.wasSuccessful()

if __name__ == "__main__":
   main()
