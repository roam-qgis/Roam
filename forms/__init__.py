__author__="WOODROWN"
__date__ ="$21/03/2012 11:45:33 AM$"

import os
import sys
from Form import Form

# Add PARENT directory to path to make test aware of other modules
pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(pardir)

def getForms():
    """ Get all the custom user forms that have been created.
    Checks for "form" at the start to detect module as custom form
    
    @Returns A list of modules that contain user forms.
    """
    modules = []
    for module in os.listdir(os.path.dirname(__file__)):
        if module[:4] == 'form':
            instance = loadFormModule(module)
            modules.append(Form(instance))
            
    return modules

def loadFormModule(module):
    """ Load the forms module """
    formmodule = __import__("SDRCDataCapture.forms.%s" % module, locals(), globals(),["*"], 1)
    return formmodule

if __name__ == "__main__":
    forms = getForms()
    from PyQt4.QtCore import QString 
    l = {'WaterJobs' : 1 , 'Cad': 2}
    for form in forms:
        value = form.layerName()
        print l
        print value
        print l[value]
        print form.formName()
        print form.layerName()
        print form.formInstance()
    # loadFormModule(forms[0])
