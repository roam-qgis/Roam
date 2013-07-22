"""
    Find and run all postinstall scripts for all the projects.
"""

import imp
import os
import fnmatch
import sys

curdir = os.path.abspath(os.path.dirname(__file__))
pardir = os.path.join(curdir, '..')
projectdir = os.path.join(pardir, "projects")

def installscripts():
    """
        Return the post install scripts for each installed project.
    """
    for root, _, filenames in os.walk(projectdir):
        for filename in fnmatch.filter(filenames, 'postinstall.py'):
            yield root, filename
            
def replaceconnections(filename, remoteserver, localserver ):
    with open(filename, 'r+') as f:
        name = os.path.basename(filename)
        print "Updating {}".format(name)
        text = f.read()
        text = text.replace('{REMOTESERVER}', remoteserver)
        text = text.replace('{LOCALSERVER}', localserver)
        f.seek(0)
        f.write(text)
        f.truncate()
    
def main(remoteserver, localserver):       
    for root, postinstall in installscripts():
        modulename = os.path.splitext(postinstall)[0]
        try:
            # Loading the source and run what ever code is in the module
            filepath = os.path.join(root, postinstall)
            postinstall_mod = imp.load_source(modulename, filepath)
        except ImportError as err:
            print "{}".format(err)
            continue
            
        try:
            # Get all the files which need to have their connection strings updated
            for filename in postinstall_mod.replace_files:
                if not os.path.exists(filename):
                    filename = os.path.join(root, '..', filename)
                replaceconnections(filename, remoteserver, localserver )
        except AttributeError:
            print "No replace files found in {}.".format(postinstall)
            continue

if __name__ == "__main__":
    print '{0:=^50}'.format('IntraMaps Roam Installer')
    try:
        remoteserver = sys.argv[1]
        localserver = sys.argv[2]
    except IndexError:
        print "No server connections supplied. You need to tell me what they are"
        remoteserver = raw_input("Remote Server: ")
        localserver = raw_input("Local Server: ")
        # Connections are passed in so we ask the installer
        
    print remoteserver, localserver
    main(remoteserver, localserver)
    
    