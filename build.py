#! /usr/bin/python

''' Build file that complies all the needed resources'''

from fabricate import *

sources = ['program', 'util']

def compile():
    

if __name__ == "__main__":
    run('pyuic4.bat', '-o', 'ui_datatimerpicker.py', 'ui_datatimerpicker.ui' )
