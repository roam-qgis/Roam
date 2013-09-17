#! /usr/bin/python
''' Build file that compiles all the needed resources'''

import os.path
import os
import sys
import datetime
import optparse
import yaml
import fabricate
import shutil

from os.path import join
from fabricate import (run, 
                       ExecutionError, 
                       shell, 
                       autoclean)

from distutils.dir_util import (copy_tree,
                                remove_tree)

APPNAME = "IntraMaps Roam"
curpath = os.path.dirname(os.path.abspath(__file__))
curpath = os.path.join(curpath, '..')
srcopyFilesath = join(curpath, "src")
appsrcopyFilesath = join(curpath, "src", 'qmap')
buildpath = join(curpath, "build", APPNAME)
targetspath = join(curpath, 'admin', 'targets.config')

doc_sources = ['docs/README', 'docs/ClientSetup', 'docs/UserGuide']

# HACK: Might not be the best thing to do but will work for now.
fabricate._set_default_builder()
fabricate.default_builder.quiet = True

def readTargetsConfig():
    try:
        with open(targetspath,'r') as f:
            config = yaml.load(f)
            return config
    except IOError:
        print "Failed to open %s" % targetspath
        return

def build():
    """
    Build the QMap plugin.  Called from the command line.
    """
    build_plugin()

def compileplugin():
    print " - building resource files..."
    run('pyrcc4', '-o', join(appsrcopyFilesath,'qtcontrols','images_rc.py'), join(appsrcopyFilesath,'qtcontrols','images.qrc'))
    run('pyrcc4', '-o', join(appsrcopyFilesath,'resources_rc.py'), join(appsrcopyFilesath,'resources.qrc'))
    run('pyrcc4', '-o', join(appsrcopyFilesath,'syncing/resources_rc.py'), join(appsrcopyFilesath,'syncing/resources.qrc'))

def docs():
    print "Generating docs"
    for doc in doc_sources:
        run('python', 'docs/rst2html.py', doc + '.rst', doc + '.html')

def clean():
    autoclean()
    remove_tree(buildpath)

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

def build_plugin():
    """
        Builds the QGIS plugin and sends the output into the build directory.
    """
    print "Deploy started"
    print "Building..."
    compileplugin()
    # Copy all the files to the ouput directory
    print "Copying new files..."
    
    copy_tree(srcopyFilesath, buildpath)

    print "Local build into {0}".format(buildpath)

def deploy():
    """ Deploy the target given via the command line """
    targetname = fabricate.main.options.target
    if targetname is None:
        print "No target name given depolying All target"
        targetname = 'All'

    deployTargetByName(targetname)

def deployTargetByName(targetname):
    """ Deploy a target usin the name found in targets.config """
    config = readTargetsConfig()
    
    try:
        target = config['clients'][targetname]
    except KeyError as ex:
        print "No client in targets.config defined as %s" % targetname
        return

    build_plugin()
    print "Deploying application to %s" % targetname
    deploytarget(target)

def deploytarget(clientconfig):    
    projects = clientconfig['projects']
    clientpath = os.path.normpath(clientconfig['path'])
    clientpath = join(clientpath, APPNAME)
    projecthome = join(curpath, 'projects')
    clientpojecthome = join(clientpath, 'projects')
    
    print "Deploying application to %s" % clientpath
    copy_tree(buildpath, clientpath)
    
    if 'All' in projects:
        copy_tree(projecthome, clientpojecthome)
    else:
        for project in projects:
            source = os.path.join(projecthome, project)
            dest = os.path.join(clientpojecthome, project)
            copy_tree(source, dest)
            
    shutil.copy2(os.path.join(projecthome, '__init__.py'), 
                               os.path.join(clientpojecthome, '__init__.py')) 
    print "Remote depoly compelete"

if __name__ == "__main__":
    options = [
        optparse.make_option('-o', '--target', dest='target', help='Target to deploy'),
    ]

    fabricate.main(extra_options=options)
