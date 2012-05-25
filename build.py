#! /usr/bin/python
''' Build file that compiles all the needed resources'''
import os.path

from fabricate import *
import os
from shutil import copytree, ignore_patterns, rmtree
import datetime

ui_sources = ['ui_datatimerpicker', 'ui_listmodules',
              'syncing/ui_sync', 'forms/ui_listfeatures']

doc_sources = ['docs/README']

# Add the path to MSBuild to PATH so that subprocess can find it.
env = os.environ.copy()
env['PATH'] += ";c:\\WINDOWS\\Microsoft.NET\Framework\\v3.5"

def build():
    compile()
    
def compile():
    print " - building UI files..."
    for source in ui_sources:
        run('pyuic4.bat', '-o', source+'.py', source+'.ui' )

    print " - building resource files..."
    run('pyrcc4', '-o', 'resources.py', 'resources.qrc')
    
    print " - building sync app..."
    run('MSBuild','/property:Configuration=Release', '/verbosity:m', \
        'syncing/SyncProofConcept.csproj', shell=True, env=env)

    print " - building docs..."
    docs()
    
def docs():
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
    pass

def deploy():
    print "Deploy started"
    print "Building..."
    compile()
    curpath = os.path.dirname(os.path.abspath(__file__))
    buildpath = os.path.join(curpath, "build", "app", "python", "plugins", \
                            "SDRCDataCollection" )
    if os.path.exists(buildpath):
        print "Removing old depoly directory..."
        rmtree(buildpath)
    
    # Copy all the files to the ouput directory
    print "Copying new files..."
    copytree(curpath, buildpath, ignore=ignore_patterns('*.pyc', 'build', \
                                                        '.git', '.deps', 'nbproject'))

    # Replace version numbers
    version = getVersion()
    run("sed", '-n','s/version=0.1/version={0}/'.format(version), \
        os.path.join(buildpath, 'metadata.txt'))
        
    print "Deploy compelete into {0}".format(buildpath)

if __name__ == "__main__":
    deploy()
    
