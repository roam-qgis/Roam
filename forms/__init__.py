__author__="WOODROWN"
__date__ ="$21/03/2012 11:45:33 AM$"

import os
from Form import *

def getForms():
    """ Get all the custom user forms that have been created.
    Checks for "form" at the start to detect module as custom form
    
    @Returns A list of modules that contain user forms.
    """
    modules = []
    for module in os.listdir(os.path.dirname(__file__)):
        if module[:4] == 'form':
            modules.append(Form(module))
            
    print modules
    return modules

def loadFormModule(form):
    """ Load the forms module """
    formmodule = __import__("SDRCDataCapture.forms.%s" % form.moduleName, locals(), globals(),["*"], 1)
    return formmodule

if __name__ == "__main__":
    forms = getForms()
    loadFormModule(forms[0])