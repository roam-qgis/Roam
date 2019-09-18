import os
import shutil
from datetime import datetime

from PyQt5.QtWidgets import QInputDialog

import roam.project
from configmanager import logger as logger

templatefolder = os.path.join(os.path.dirname(__file__), "templates")


def newfoldername(basetext, basefolder, formtype, alreadyexists=False):
    message = "Please enter a new folder name for the {}".format(formtype)
    if alreadyexists:
        logger.log("Folder {} already exists.")
        message += "<br> {} folder already exists please select a new one.".format(formtype)

    name, ok = QInputDialog.getText(None, "New {} folder name".format(formtype), message)
    if not ok:
        raise ValueError

    if not name:
        return "{}_{}".format(basetext, datetime.today().strftime('%d%m%y%f'))
    else:
        name = name.replace(" ", "_")

    if os.path.exists(os.path.join(basefolder, name)):
        return newfoldername(basetext, basefolder, formtype, alreadyexists=True)

    return name


def newproject(projectfolder):
    """
    Create a new folder in the projects folder.
    :param projectfolder: The root project folder
    :return: The new project that was created
    """
    foldername = newfoldername("project", projectfolder, "Project")
    templateproject = os.path.join(templatefolder, "templateProject")
    newfolder = os.path.join(projectfolder, foldername)
    shutil.copytree(templateproject, newfolder)
    project = roam.project.Project.from_folder(newfolder)
    project.settings['title'] = foldername
    return project


def newform(project):
    folder = project.folder
    foldername = newfoldername("form", folder, "Form")

    formfolder = os.path.join(folder, foldername)
    templateform = os.path.join(templatefolder, "templateform")
    shutil.copytree(templateform, formfolder)

    config = dict(label=foldername, type='auto', widgets=[])
    form = project.addformconfig(foldername, config)
    logger.debug(form.settings)
    logger.debug(form.settings == config)
    return form