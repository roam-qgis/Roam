#! /usr/bin/python

''' Build file that complies all the needed resources'''
import os.path

from fabricate import *
import os
from shutil import copytree, ignore_patterns, rmtree

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
    print "Building..."
    compile()
    curpath = os.path.dirname(__file__)
    buildpath = os.path.join(curpath, "build", "app", "python", "plugins", \
                            "SDRCDataCollection" )
    if os.path.exists(buildpath):
        print "Removing old depoly directory..."
        rmtree(buildpath)
    # Copy all the files to the ouput directory
    print "Copying new files..."
    copytree(curpath, buildpath, ignore=ignore_patterns('*.pyc', 'build', \
                                                        '.git', '.deps' ))

    print "Deploy compelete into {0}".format(buildpath)

if __name__ == "__main__":
    deploy()
    
