#! /usr/bin/python
''' Build file that compiles all the needed resources'''

import os.path
import os
import sys
import datetime
import optparse
import fabricate
import shutil

from os.path import join
from fabricate import (run, 
                       ExecutionError, 
                       shell, 
                       autoclean)

curpath = os.path.dirname(os.path.abspath(__file__))
appsrcopyFilesath = join(curpath, "src", 'roam')

doc_sources = ['docs/README', 'docs/ClientSetup', 'docs/UserGuide']

# HACK: Might not be the best thing to do but will work for now.
fabricate._set_default_builder()
fabricate.default_builder.quiet = True

def builduifiles():
    for root, dirs, files in os.walk(appsrcopyFilesath):
        for file in files:
            if file.endswith('.ui'):
                uipath = os.path.join(root, file)
                pypath = join(root, file[:-3] + '.py')
                run('pyuic4.bat', '-o', pypath, uipath, shell=True)

def build():
    print " - building resource files..."
    path = join(appsrcopyFilesath, 'editorwidgets', "uifiles")
    run('pyrcc4', '-o', join(path, 'images_rc.py'), join(path, 'images.qrc'))
    run('pyrcc4', '-o', join(appsrcopyFilesath,'resources_rc.py'), join(appsrcopyFilesath,'resources.qrc'))
    run('pyrcc4', '-o', join(appsrcopyFilesath,'syncing/resources_rc.py'), join(appsrcopyFilesath,'syncing/resources.qrc'))
    print " - building UI files...."
    builduifiles()

def docs():
    print "Generating docs"
    for doc in doc_sources:
        run('python', 'docs/rst2html.py', doc + '.rst', doc + '.html')

def clean():
    autoclean()

def getVersion():
    """
        Returns the version number for the plugin
    """
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    try:
        commit = shell('git', 'log', '-1', '--pretty=%h').strip()
    except WindowsError:
        commit = ""
    except ExecutionError:
        commit = ""
    return "{0}.{1}.{2}.{3}".format(year, month, day, commit)

def test():
    """
        Run the tests in the project
    """
    print "Running tests..."
    import unittest
    from src import tests
    loader = unittest.TestLoader()
    allsuite = loader.loadTestsFromModule(tests)
    result = unittest.TextTestRunner().run(allsuite)
    return result.wasSuccessful()

if __name__ == "__main__":
    fabricate.main()
