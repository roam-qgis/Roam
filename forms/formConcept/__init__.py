__author__="WOODROWN"
__date__ ="$21/03/2012 2:20:26 PM$"

from PyQt4 import uic
import os

__formName__ = "Concept Form"
__layerName__ = "ProofConcept"
__mapTool__ = None
__mapToolType__ = "POINT"

def dialogInstance():
    curdir= os.path.dirname(__file__)
    path =os.path.join(curdir,'ui_concept.ui')
    return uic.loadUi(path)