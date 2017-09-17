import os
import sys

# Add parent directory to path to make test aware of other modules
srcfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', "src"))
if srcfolder not in sys.path:
    sys.path.append(srcfolder)


