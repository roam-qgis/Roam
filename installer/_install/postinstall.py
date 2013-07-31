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

# List of files with connection information for update
replace_files = ['setenv.bat']

def installscripts():
    """
        Return the post install scripts for each installed project.
    """
    for root, _, filenames in os.walk(projectdir):
        for filename in fnmatch.filter(filenames, 'postinstall.py'):
            yield root, filename
            
def replaceconnections(filename, **mappings ):
    with open(filename, 'r+') as f:
        name = os.path.basename(filename)
        print "Updating {}".format(name)
        text = f.read()
        for token, value in mappings.items():
            text = text.replace('{{0}}'.format(token), value)
        f.seek(0)
        f.write(text)
        f.truncate()
        
def replace_files(root, files, **mappings):
    # Get all the files which need to have their connection strings updated
    for filename in files:
        if not os.path.exists(filename):
            filename = os.path.join(root, '..', filename)
        try:
            replaceconnections(filename, mappings )
        except IOError:
            print "Error reading file"
            print filename
    
def main(**mappings):
    # Replace the files in root first
    replace_files(pardir, replace_files, **mappings)
    
    # Run the post install scripts for each installed project.
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
            # Get all the files that need values replaced.
            replace_files(root, postinstall_mod.replace_files, **mappings)
        except AttributeError:
            print "No replace files found in {}.".format(postinstall)
            continue

if __name__ == "__main__":
    print '{0:=^50}'.format('IntraMaps Roam Installer')  
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote_server", help="Path to the remove server")
    parser.add_argument("--local_server", help="Path to the remove server")
    
    args = parser.parse_args()
    
    if args.remote_server is None or args.local_server is None:
        print "Some of the installer options are missing."
        print "You need to tell me what they are before IntraMaps Roam"
        print "can be installed correctly"
        print
        remoteserver = raw_input("Remote Server: ")
        localserver = raw_input("Local Server: ")
    else:
        remoteserver = args.remote_server
        localserver = args.local_server
    
    print '{0:=^50}'.format('Using the following settings')
    print remoteserver
    print localserver
    print '{0:=^50}'.format('=')
        
    main(REMOTESERVER=remoteserver, LOCALSERVER=localserver)
    
    