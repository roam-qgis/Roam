import os
import shutil
from datetime import datetime

from PyQt5.QtWidgets import QInputDialog

import roam.project
from configmanager import logger as logger

templatefolder = os.path.join(os.path.dirname(__file__), "templates")


def directory_exsits(name, basefolder):
    """
    Check if the
    :param name:
    :param basefolder:
    :return:
    """
    return os.path.exists(os.path.join(basefolder, name))


def new_directory_name(name, basetext=None):
    """
    Create a new safe directory name
    :param name: The name of the new folder. Replaces any unsafe folder names with a safe values.
    :param basetext: The default
    :return:
    """
    if not name:
        return "{}_{}".format(basetext, datetime.today().strftime('%d%m%y%f'))
    else:
        return name.replace(" ", "_")


def create_project(projectfolder, name):
    """
    Create a new folder in the projects folder.
    :param projectfolder: The root project folder
    :return: The new project that was created
    """
    templateproject = os.path.join(templatefolder, "templateProject")
    newfolder = os.path.join(projectfolder, name)
    shutil.copytree(templateproject, newfolder)
    project = roam.project.Project.from_folder(newfolder)
    project.settings['title'] = name
    return project


def create_form(project, name):
    folder = project.folder

    formfolder = os.path.join(folder, name)
    templateform = os.path.join(templatefolder, "templateform")
    shutil.copytree(templateform, formfolder)

    config = dict(label=name, type='auto', widgets=[])
    form = project.addformconfig(name, config)
    logger.debug(form.settings)
    logger.debug(form.settings == config)
    return form