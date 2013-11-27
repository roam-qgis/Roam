__author__="WOODROWN"
__date__ ="$21/03/2012 11:48:53 AM$"

import unittest
import forms

import forms.formWater

class testForms(unittest.TestCase):
    def testGetFormsReturnsCorrectNumber(self):
        listofforms = forms.getForms()
        self.assertEqual(1, len(listofforms))

    def testFormShouldHaveCorrectName(self):
        listofforms = forms.getForms()
        self.assertEqual("formWater", listofforms[0].moduleName)

    def testFormsShouldImportCorrectlyAndGetName(self):
        listofforms = forms.getForms()
        loaded = forms.loadFormModule(listofforms[0])

        self.assertEqual("Water Form", loaded.name())
        
if __name__ == "__main__":
    unittest.main()