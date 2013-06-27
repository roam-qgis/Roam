#! /usr/bin/python
''' Build file that compiles all the needed resources'''

import os.path
import os
import sys
import datetime
import optparse
import json
import fabricate

from os.path import join
from fabricate import (run, 
                       ExecutionError, 
                       shell, 
                       autoclean)

from distutils.dir_util import (copy_tree,
                                remove_tree)

APPNAME = "QMap"
curpath = os.path.dirname(os.path.abspath(__file__))
curpath = os.path.join(curpath, '..')
srcopyFilesath = join(curpath, "src", "qmap")
buildpath = join(curpath, "build", APPNAME)
deploypath = join(curpath, "build", APPNAME, "qmap")
targetspath = join(curpath, 'qmap-admin', 'targets.config')
bootpath = join(curpath, "src", "loader_src")
dotnetpath = join(curpath, "src", "dotnet")

ui_sources = ['ui_datatimerpicker', 'ui_listmodules',
              'syncing/ui_sync', 'ui_listfeatures', 'ui_errorlist',
              'ui_helpviewer','ui_drawingpad', "ui_helppage"]

doc_sources = ['docs/README', 'docs/ClientSetup', 'docs/UserGuide']

iswindows = os.name == 'nt'

# HACK: Might not be the best thing to do but will work for now.
fabricate._set_default_builder()
fabricate.default_builder.quiet = True

if iswindows:
    # Add the path to MSBuild to PATH so that subprocess can find it.
    env = os.environ.copy()
    env['PATH'] += ";c:\\WINDOWS\\Microsoft.NET\Framework\\v3.5"

def readTargetsConfig():
    try:
        with open(targetspath,'r') as f:
            config = json.load(f)
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
    print " - building UI files..."
    for source in ui_sources:
        pyuic = 'pyuic4'
        if iswindows:
            pyuic += '.bat'
        source = join(srcopyFilesath, source)
        run(pyuic, '-o', source + '.py', source + '.ui')

    print " - building resource files..."
    run('pyrcc4', '-o', join(srcopyFilesath,'resources_rc.py'), join(srcopyFilesath,'resources.qrc'))
    run('pyrcc4', '-o', join(srcopyFilesath,'syncing/resources_rc.py'), join(srcopyFilesath,'syncing/resources.qrc'))

    if iswindows:
        try:
            projects = ['libsyncing/libsyncing.csproj', 
                        'provisioner/provisioner.csproj',
                        'syncer/syncer.csproj']
    
            print " - building syncing tools..."
            for project in projects:
                run('MSBuild', '/property:Configuration=Release', '/verbosity:m', \
                join(dotnetpath, project), shell=False, env=env)
    
            mssyncpath = os.path.join(dotnetpath, "bin")
            lib = os.path.join(mssyncpath, "libsyncing.dll")
            bin = os.path.join(mssyncpath, "provisioner.exe")
            clientsetuppath = os.path.join(curpath,"qmap-admin","client-setup")
            copy_tree(lib, clientsetuppath)
            copy_tree(bin, clientsetuppath)
        except ExecutionError:
            pass
        except WindowsError:
            pass

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
    
    copy_tree(srcopyFilesath,deploypath)
    copy_tree(bootpath,buildpath)

    if iswindows:
        mssyncpath = join(dotnetpath, "bin")
        lib = join(mssyncpath, "libsyncing.dll")
        bin = join(mssyncpath, "syncer.exe")
        destmssyncpath = join(deploypath,"syncing")
        if os.path.exists(lib) and os.path.exists(bin):
            copy_tree(lib, destmssyncpath)
            copy_tree(bin, destmssyncpath)
    # Replace version numbers
    version = getVersion()
    command = 's/version=0.1/version=%s/ "%s"' % (version, join(deploypath, 'metadata.txt'))
    #run("sed", command)

    print "Local build into {0}".format(deploypath)

def deploy():
    """ Deploy the target given via the command line """
    targetname = main.options.target
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
            
    print "Remote depoly compelete"

if __name__ == "__main__":
    options = [
        optparse.make_option('-o', '--target', dest='target', help='Target to deploy'),
        # optparse.make_option('--with-tests', action='store', help='Enable tests!', \
        #                      default=True),
        # optparse.make_option('--with-mssyncing', action='store', help='Use MS SQL Syncing!', \
        #                      default=True),
		# optparse.make_option('--with-docs', action='store', help='Build docs', \
  #                            default=True)
    ]

    main(extra_options=options)
