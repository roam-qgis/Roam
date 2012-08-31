#! /usr/bin/python
''' Build file that compiles all the needed resources'''
import os.path

import os
import sys
import nose
import datetime
from shutil import copytree, ignore_patterns, rmtree
from fabricate import *
from subprocess import Popen, PIPE
from PyQt4.QtGui import QApplication
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from nose.plugins.cover import Coverage

ui_sources = ['src/ui_datatimerpicker', 'src/ui_listmodules',
              'src/syncing/ui_sync', 'src/ui_listfeatures', 'src/ui_errorlist']

doc_sources = ['docs/README', 'docs/ClientSetup']

path = os.path.dirname(__file__)

# Add the path to MSBuild to PATH so that subprocess can find it.
env = os.environ.copy()
env['PATH'] += ";c:\\WINDOWS\\Microsoft.NET\Framework\\v3.5"

APPNAME = "QMap"
EXCLUDES = '/EXCLUDE:excludes.txt'

curpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(curpath, "src")
pluginpath = os.path.join(APPNAME, "app", "python", "plugins", \
                            APPNAME)
buildpath = os.path.join(curpath, pluginpath )
targetspath = os.path.join(curpath,'targets.ini')
                            
deploypath = os.path.join(curpath, APPNAME)
bootpath = os.path.join('src', "boot")

args = ['/D', '/S', '/E', '/K', '/C', '/H', '/R', '/Y', '/I']

def build():
    deploy_to_clients()
    
def compile():
    print " - building UI files..."
    for source in ui_sources:
        run('pyuic4.bat', '-o', source+'.py', source+'.ui' )

    print " - building resource files..."
    run('pyrcc4', '-o', 'src/resources_rc.py', 'src/resources.qrc')
    run('pyrcc4', '-o', 'src/syncing/resources_rc.py', 'src/syncing/resources.qrc')
    
    print " - building MSSQLSyncer app..."
    run('MSBuild','/property:Configuration=Release', '/verbosity:m', \
        'src/syncing/MSSQLSyncer/MSSQLSyncer.csproj', shell=True, env=env)

    print " - building Provisioning app..."
    run('MSBuild','/property:Configuration=Release', '/verbosity:m', \
        'provisioner/SqlSyncProvisioner/SqlSyncProvisioner.csproj', \
        shell=True, env=env)

    print " - building docs..."
    docs()
    
def docs():
    print "Generating docs"
    for doc in doc_sources:
        run('python', 'docs/rst2html.py', doc+'.txt', doc+'.html')

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
    commit = shell('git', 'log', '-1', '--pretty=%h').strip()
    return "{0}.{1}.{2}.{3}".format(year, month, day, commit )

def test():
    import nose
    return nose.run()

def deploy_local():
    print "Deploy started"
    print "Building..."
    compile()
    passed = test()
    if not passed:
        print "Tests Failed!!"
        return False
   
    # Copy all the files to the ouput directory
    print "Copying new files..."
    msg = shell('xcopy',srcpath, buildpath, args, EXCLUDES ,silent=False)
                                   
    msg = shell('xcopy',bootpath, deploypath, args ,silent=False)

    # Replace version numbers
    version = getVersion()
    run("sed", '-i','s/version=0.1/version={0}/'.format(version), \
        os.path.join(buildpath, 'metadata.txt'))
        
    print "Local depoly compelete into {0}".format(buildpath)
    return True

def deploy_to(target, config):
    print "Remote depolying to %s" % target

    projects = config['projects']
    forms = config['forms']
    clientpath = os.path.normpath(config['client'])

    
    print "Deploying application to %s" % config['client']
    clientapppath = os.path.join(clientpath, APPNAME)
    msg = shell('xcopy', deploypath, clientapppath, args \
                ,'/EXCLUDE:depoly_excludes.txt',silent=False)
                
    projectpath = os.path.join(buildpath,'projects')
    clientpojectpath = os.path.join(clientpath,pluginpath,'projects')
    formpath = os.path.join(buildpath,'entry_forms')
    clientformpath = os.path.join(clientpath,pluginpath,'entry_forms')

    msg = shell('xcopy', projectpath, clientpojectpath, '/T','/E','/I','/Y' ,silent=False)
    msg = shell('xcopy', formpath, clientformpath,'/I','/Y', '/D' ,silent=False)
    
    if 'All' in projects:
        print "Loading all projects"
        msg = shell('xcopy', projectpath, clientpojectpath, args ,silent=False)
    else:
        for project in projects:
            if project and project[-4:] == ".qgs":
                print "Loading project %s" % project
                path = os.path.join(projectpath, project)
                newpath = os.path.join(clientpojectpath, project)
                msg = shell('copy',path, newpath, '/Y', silent=False, shell=True)

    if 'All' in forms:
        print "Loading all forms"
        msg = shell('xcopy', formpath, clientformpath, args ,silent=False)
    else:
        for form in forms:
            if form:
                print "Loading form %s" % form
                path = os.path.join(formpath, form)
                newpath = os.path.join(clientformpath, form)
                msg = shell('xcopy', path, newpath, args ,silent=False)
        
    print "Remote depoly compelete"

def deploy_target(targetname, config):
    print targetname
    targets = {}
    try:
        clients = config.get(targetname,'client').split(',')
        for client in clients:
            client = client.strip()
            if client == targetname:
                print "Can't include a section as a deploy target of itself"
                continue
                
            if client in config.sections():
                deploy_target(client, config)
            else:
                print 'Client -> %s' % client
                projects = config.get(targetname,'projects').split(',')
                forms = config.get(targetname,'forms').split(',')
                targets[targetname] = {'client': client, 'projects' : projects, \
                                 'forms' : forms }
            
            for target, items in targets.iteritems():
                deploy_to(target, items)
                
    except NoSectionError as ex:
        print ex.message
    except NoOptionError as ex:
        print ex.message

if __name__ == "__main__":
    from mock import patch
    with patch('build.deploy_to') as mock:
        config = ConfigParser()
        config.read(targetspath)
        deploy_local()
        deploy_target('All', config)
    sys.exit()
