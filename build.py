#! /usr/bin/python

''' Build file that complies all the needed resources'''

from fabricate import *
import os

ui_sources = ['ui_datatimerpicker', 'ui_listmodules',
              'syncing/ui_sync', 'forms/ui_listfeatures']

def build():
    compile()
    
def compile():
    for source in ui_sources:
        run('pyuic4.bat', '-o', source+'.py', source+'.ui' )

    run('pyrcc4', '-o', 'resources.py', 'resources.qrc')

def clean():
    autoclean()

def deploy():
    curpath = os.path.dirname(__file__)
    buildpath = os.path.join(curpath, "build", "app", "python", "plugins", \
                            "SDRCDataCollection" )
    os.makedirs(buildpath)
    
    
if __name__ == "__main__":
    main()
    
