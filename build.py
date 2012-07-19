#! /usr/bin/python
''' Build file that compiles all the needed resources'''
import os.path

from fabricate import *
import os
import sys
from shutil import copytree, ignore_patterns, rmtree
import datetime
from subprocess import Popen, PIPE
from PyQt4.QtGui import QApplication

import nose
from nose.plugins.cover import Coverage

ui_sources = ['src/ui_datatimerpicker', 'src/ui_listmodules',
              'src/syncing/ui_sync', 'src/ui_listfeatures', 'src/ui_errorlist']

doc_sources = ['docs/README', 'docs/ClientSetup']

path = os.path.dirname(__file__)

# Add the path to MSBuild to PATH so that subprocess can find it.
env = os.environ.copy()
env['PATH'] += ";c:\\WINDOWS\\Microsoft.NET\Framework\\v3.5"

curpath = os.path.dirname(os.path.abspath(__file__))
srcpath = os.path.join(curpath, "src")
buildpath = os.path.join(curpath, "SDRCDataCollection", "app", "python", "plugins", \
                            "SDRCDataCollection" )
                            
deploypath = os.path.join(curpath, "SDRCDataCollection")
bootpath = os.path.join('src', "boot") 

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

def deploy():
    print "Deploy started"
    print "Building..."
    compile()
    passed = test()
    if not passed:
        print "Tests Failed!!"
        return False
   
    # Copy all the files to the ouput directory
    print "Copying new files..."
    msg = shell('xcopy',srcpath, buildpath, '/D', '/S', '/E', '/K', '/C', '/H', \
                                   '/R', '/Y','/EXCLUDE:excludes.txt',silent=False)                         
                                   
    msg = shell('xcopy',bootpath, deploypath, '/D', '/S', '/E', '/K', '/C', '/H', \
                                   '/R', '/Y',silent=False)

    # Replace version numbers
    version = getVersion()
    run("sed", '-i','s/version=0.1/version={0}/'.format(version), \
        os.path.join(buildpath, 'metadata.txt'))
        
    print "Local depoly compelete into {0}".format(buildpath)
    return True

def deploy_to(client, rebuild=True):
    if rebuild:
        if not deploy(): return

    print "Remote depolying to %s" % client
    
    deploypath = os.path.join(curpath, "SDRCDataCollection")
    msg = shell('xcopy',deploypath, client, '/D', '/S', '/E', '/K', '/C', '/H', \
                                   '/R', '/Y',silent=False)
   
    print "Remote depoly compelete"

def deploy_to_clients():
    clients = ['\\\\sd0469\\C$\\Users\\woodrown\\Desktop\\SDRCDataCollection\\',]
               #'\\\\sd0496\\C$\\Users\\woodrown\\Desktop\\SDRCDataCollection\\']

    rebuild = True
    for client in clients:
        deploy_to(client, rebuild)
        # Turn rebuild off so we only do it once.
        rebuild = False

main()