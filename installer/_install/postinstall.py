"""
    Post install script for IntraMaps Roam
"""

import imp
import os
import fnmatch
import sys
import shutil
import logging

curdir = os.path.abspath(os.path.dirname(__file__))
pardir = os.path.join(curdir, '..')

def installscripts(rootfolder):
    """
        Return the post install scripts for each installed project.
    """
    for root, _, filenames in os.walk(rootfolder):
        for filename in fnmatch.filter(filenames, 'postinstall.py'):
            yield root, filename
            
def templatefiles(rootfolder):
    """
        Return the template files and new name for each tmpl in a 
        given rootfolder.
    """
    for root, _, filenames in os.walk(rootfolder):
        for filename in fnmatch.filter(filenames, '*.tmpl'):
            template = os.path.join(root, filename)
            newfile = os.path.splitext(template)[0]       
            yield template, newfile
    
def replace_tokens(filename, tokens ):
    """
        Replace all the tokens in the file 
        Tokens given as keyword args
    """
    with open(filename, 'r+') as f:
        text = f.read()
        for token, value in tokens.items():
            token = '{{{0}}}'.format(token)
            text = text.replace(token, value)
        f.seek(0)
        f.write(text)
        f.truncate()
        
def replace_tokens_in_files(root, files, tokens):
    """
        Replace all the tokens in the given files.
    """
    # Get all the files which need to have their connection strings updated
    for filename in files:
        if not os.path.exists(filename):
            filename = os.path.join(root, '..', filename)
        try:
            replace_tokens(filename, tokens )
        except IOError as err:
            print "Error reading file"
            print filename
            print err
    
def main(**tokens):   
    projectdir = os.path.join(pardir, "projects")

    logger.info('{0:=^50}'.format('Copying template files'))
    # Create a real file for each template file in project file.
    for template, newfile in templatefiles(projectdir):
        shutil.copy2(template, newfile)
        replace_tokens(newfile, tokens )
        logger.info("Updated {}".format(os.path.basename(newfile)))
     
    logger.info('{0:=^50}'.format('Running post install scripts'))
    # Run the post install scripts for each installed project.
    for root, postinstall in installscripts(projectdir):
        modulename = os.path.splitext(postinstall)[0]
        try:
            # Loading the source and run what ever code is in the module
            filepath = os.path.join(root, postinstall)
            postinstall_mod = imp.load_source(modulename, filepath)
        except ImportError as err:
            logger.error("{}".format(err))
            continue

if __name__ == "__main__":
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    consolelogger = logging.StreamHandler()
    consolelogger.setLevel(logging.INFO)
    consolelogger_format = logging.Formatter('%(message)s')
    consolelogger.setFormatter(consolelogger_format)
    logger.addHandler(consolelogger)
    
    filelogger = logging.FileHandler("installer.log")
    filelogger.setLevel(logging.DEBUG)
    filelogger_format = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
    filelogger.setFormatter(filelogger_format)
    logger.addHandler(filelogger)
    
    logger.info('{0:=^50}'.format('IntraMaps Roam Installer'))
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote_server", help="Path to the remove server")
    parser.add_argument("--local_server", help="Path to the remove server")
    
    args = parser.parse_args()
    
    if args.remote_server == 'None' or args.local_server == 'None':
        print "Some of the installer options are missing."
        print "You need to tell me what they are before IntraMaps Roam"
        print "can be installed correctly"
        print
        remoteserver = raw_input("Remote Server: ")
        localserver = raw_input("Local Server: ")
    else:
        remoteserver = args.remote_server
        localserver = args.local_server
    
    logger.info('{0:=^50}'.format('Using the following settings'))
    logger.info(remoteserver)
    logger.info(localserver)
    logger.info('{0:=^50}'.format('='))
        
    main(REMOTESERVER=remoteserver, LOCALSERVER=localserver)
    
    