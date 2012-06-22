import os.path
#! /usr/bin/python
import parser
import os
from string import Template

__author__="WOODROWN"
__date__ ="$19/04/2012 2:49:46 PM$"

from optparse import OptionParser

initstring = Template("""from PyQt4 import QtGui
from ui_$(ui) import Ui_WaterForm

__formName__ = '$name'
__layerName__ = '$layer'
__mapTool__ = None
__mapToolType__ = 'POINT'

def dialogInstance():
    return MyDialog()

class Dialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_WaterForm()
        self.ui.setupUi(self)""")

compliestring = Template("pyuic4 -o ui_$py.py $ui")

if __name__ == "__main__":
    """
        Helper to create the form folder structure with the correct layer and files
    """
    
    parser = OptionParser()
    parser.add_option("-f", "--folder", dest="foldername",
                      help="Overwrite folder name for form folder", metavar="NAME")

    (options, args) = parser.parse_args()

    if not len(args) == 3:
        parser.error("incorrect number of arguments")
        
    filename = args[0]
    layer = args[1]
    name = args[2]
    if not filename[-3:] == ".ui":
        parser.error("incorrect number of arguments")
        
    newfilename = filename.replace(" ", "")
    print filename
    foldername = "form%s" % (options.foldername or newfilename[:-3])
    print foldername
    if not os.path.exists(foldername):
        os.makedirs(foldername)

    os.rename(filename, os.path.join(foldername, newfilename))

    with open(os.path.join(foldername, '__init__.py'), 'w') as f:
        string = initstring.safe_substitute(name=name,layer=layer, ui=newfilename[:-3])
        f.write(string)

    with open(os.path.join(foldername, 'build.bat'), 'w') as f:
        string = compliestring.safe_substitute(py=newfilename[:-3],ui=newfilename)
        f.write(string)