"""
    Post install script for IntraMaps Roam
"""

import imp
import os
import fnmatch
import sys
import shutil
import logging
import re
import roam.yaml

from string import Template

curdir = os.path.abspath(os.path.dirname(__file__))
pardir = os.path.join(curdir, '..')
projectdir = os.path.join(pardir, "projects")

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

# TODO This could be done with the string.Template class
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

# TODO We could use the string.Template class to get tokens
def get_tokens(filename):
    """
    Return the tokens in the file that can be used by the installer
    to update the files.
    """
    with open(filename, 'r') as f:
        text = f.read()
    
    return set(re.findall('{(.*?)}', text))

def get_project_tokens(folder):
    tokens = set()
    for templatefile, _ in templatefiles(folder):
        filetokens = get_tokens(templatefile)
        tokens.update(filetokens)
    return tokens

def sort_tokens(tokens):
    def token_key(token):
        try:
            order = token.split()
            return int(order[0])
        except ValueError:
            return token
        
    return sorted(tokens, key=token_key)
        
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
    
def main(tokens):
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
    parser.add_argument("--save", 
                        action='store_true', 
                        help="Save the values after the installer has been completed")
    
    args = parser.parse_args()
    
    tokens = sort_tokens(get_project_tokens(projectdir))
    
    print 
    logger.info('{0:=^50}'.format('Values for installer'))
    map(logger.info, tokens)
        
    print 
    logger.info('{0:=^50}'.format('Please update each installer value'))
    updatedtokens = {}
    for token in tokens:
        value = raw_input("{}: ".format(token))
        updatedtokens[token] = value
    
    print 
    logger.info('{0:=^50}'.format('Using the following settings'))
    for key, value in updatedtokens.items():
        logger.info("{} = {}".format(key, value))
    logger.info('{0:=^50}'.format('='))
        
    main(updatedtokens)
    
    if args.save:
        path = os.path.join(curdir, 'installervalues.txt')
        with open(path, 'w') as f:
            roam.yaml.dump(data=updatedtokens, stream=f, default_flow_style=False)