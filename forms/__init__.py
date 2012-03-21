__author__="WOODROWN"
__date__ ="$21/03/2012 11:45:33 AM$"

import os
from Form import *

def getForms():
    modules = []
    for module in os.listdir(os.path.dirname(__file__)):
        if module[:4] == 'form':
            modules.append(Form(module))
            
    print modules
    return modules

def loadForm(form):
    formmodule = __import__("forms.%s" % form.moduleName, locals(), globals(),["*"], 1)
    return formmodule

if __name__ == "__main__":
    forms = getForms()
    loadForm(forms[0])