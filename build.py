#! /usr/bin/python
''' Build file that compiles all the needed resources'''
import os.path
from os.path import join
import os
import sys
import datetime
from fabricate import *
import optparse
import json

APPNAME = "QMap"
curpath = os.path.dirname(os.path.abspath(__file__))
srcopyFilesath = join(curpath, "src", "plugin")
buildpath = join(curpath, "build", APPNAME)
deploypath = join(curpath, "build", APPNAME, APPNAME.lower())
targetspath = join(curpath, 'targets.config')
bootpath = join(curpath, "src", "loader_src")
dotnetpath = join(curpath, "src", "dotnet")

ui_sources = ['ui_datatimerpicker', 'ui_listmodules',
              'syncing/ui_sync', 'ui_listfeatures', 'ui_errorlist',
              'ui_helpviewer']

doc_sources = ['docs/README', 'docs/ClientSetup', 'docs/UserGuide']

path = os.path.dirname(__file__)

flags = '--update -rvp'.split()

iswindows = os.name == 'nt'

if iswindows:
    # Add the path to MSBuild to PATH so that subprocess can find it.
    env = os.environ.copy()
    env['PATH'] += ";c:\\WINDOWS\\Microsoft.NET\Framework\\v3.5"

def build():
    """
    Build the project.
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

    if iswindows and main.options.with_mssyncing == True:
        projects = ['libsyncing/libsyncing.csproj', 
                    'provisioner/provisioner.csproj',
                    'syncer/syncer.csproj']

        print " - building syncing tools..."
        for project in projects:
            run('MSBuild', '/property:Configuration=Release', '/verbosity:m', \
            join(dotnetpath, project), shell=True, env=env)

        mssyncpath = os.path.join(dotnetpath, "bin")
        lib = os.path.join(mssyncpath, "libsyncing.dll")
        bin = os.path.join(mssyncpath, "provisioner.exe")
        syncbin = os.path.join(mssyncpath, "syncer.exe")
        clientsetuppath = os.path.join(curpath,"client-manager","client-setup")
        copyFiles(mssyncpath, clientsetuppath)

    print " - building docs..."
    docs()


def docs():
    if main.options.with_docs == True:
		print "Generating docs"
		for doc in doc_sources:
			run('python', 'docs/rst2html.py', doc + '.rst', doc + '.html')


def clean():
    autoclean()
    msg = shell('rm', '-r', buildpath)


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
    if main.options.with_tests == True:
        passed = test()
        if not passed:
            print "Tests Failed!!"
            sys.exit()

    # Copy all the files to the ouput directory
    print "Copying new files..."

    mkdir(deploypath)
    copyFiles(srcopyFilesath,deploypath)
    copyFiles(bootpath,buildpath)

    if iswindows and main.options.with_mssyncing == True:
        mssyncpath = join(dotnetpath, "bin")
        lib = join(mssyncpath, "libsyncing.dll")
        bin = join(mssyncpath, "syncer.exe")
        destmssyncpath = join(deploypath,"syncing")
        copyFolder(lib, destmssyncpath)
        copyFolder(bin, destmssyncpath)
    # Replace version numbers
    version = getVersion()
    command = 's/version=0.1/version=%s/ "%s"' % (version, join(deploypath, 'metadata.txt'))
    #run("sed", command)

    print "Local build into {0}".format(deploypath)

def copyFiles(src, dest):
    src = os.path.join(src,'*')
    if iswindows:
        src = src.replace('\\','/')
        dest = dest.replace('\\','/')
    msg = shell('cp', flags, src , dest, shell=True, silent=False)

def copyFolder(src, dest):
    if iswindows:
        src = src.replace('\\','/')
        dest = dest.replace('\\','/')
    msg = shell('cp', flags, src, dest, shell=True, silent=False)

def mkdir(path):
    if iswindows:
        path = path.replace('\\','/')
    msg = shell('mkdir', '-p', path, silent=False)

def deploy():
    targetname = main.options.target
    if targetname is None:
        print "No target name given depolying All target"
        targetname = 'All'

    try:
        with open(targetspath,'r') as f:
            config = json.load(f)
    except IOError:
        print "Failed to open %s" % targetspath
        return

    try:
        clients = config['clients'][targetname]
    except KeyError as ex:
        print "No client in targets.config defined as %s" % targetname
        return

    build_plugin()
    target = config['clients'][targetname]
    print "Deploying application to %s" % targetname
    deploytarget(target)

def deploytarget(clientconfig):
    projects = clientconfig['projects']
    forms = clientconfig['forms']
    clientpath = os.path.normpath(clientconfig['path'])

    print "Deploying application to %s" % clientpath
    clientpath = os.path.join(clientpath, APPNAME)
    mkdir(clientpath)
    copyFiles(buildpath,clientpath)

    projecthome = os.path.join(curpath, 'client-manager', 'projects')
    clientpojecthome = os.path.join(clientpath, APPNAME.lower(), 'projects')

    print projecthome

    formpath = os.path.join(curpath, 'client-manager', 'entry_forms')
    clientformpath = os.path.join(clientpath, APPNAME.lower(), 'entry_forms')

    print formpath

    mkdir(clientpojecthome)
    mkdir(clientformpath)

    if 'All' in projects:
        print "Loading all projects"
        copyFiles(projecthome, clientpojecthome )
    else:
        for project in projects:
            if project and project[-4:] == ".qgs":
                print "Loading project %s" % project
                path = os.path.join(projecthome, project)
                newpath = os.path.join(clientpojecthome, project)
                copyFolder(path, newpath)
                icon = project[:-4] + ".png"
                path = os.path.join(projecthome, icon)
                newpath = os.path.join(clientpojecthome, icon)
                if os.path.exists(path):
                    copyFolder(path, newpath)
                else:
                    print "No project image. Ignoring"

    if 'All' in forms:
        print "Loading all forms"
        copyFiles(formpath, clientformpath )
    else:
        for form in forms:
            if form:
                print "Loading form %s" % form
                path = os.path.join(formpath, form)
                newpath = os.path.join(clientformpath, form)
                if os.path.exists(newpath):
                    copyFiles(path, newpath )
                else:
                    copyFolder(path, newpath)

    print "Remote depoly compelete"

if __name__ == "__main__":
    options = [
        optparse.make_option('-o', '--target', dest='target', help='Target to deploy'),
        optparse.make_option('--with-tests', action='store', help='Enable tests!', \
                             default=True),
        optparse.make_option('--with-mssyncing', action='store', help='Use MS SQL Syncing!', \
                             default=True),
		optparse.make_option('--with-docs', action='store', help='Build docs', \
                             default=True)
    ]

    main(extra_options=options)
