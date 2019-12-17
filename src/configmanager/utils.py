import sys
import os
import subprocess
import roam.config

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices

from jinja2 import Environment, FileSystemLoader
from qgis.core import Qgis

path = os.path.join(os.path.dirname(__file__), "templates", "html")

env = Environment(loader=FileSystemLoader(path))


class QGISNotFound(Exception):
    def __init__(self, locations):
        self.message = "Can't find installed QGIS in: {}".format(locations)


def qgis_path(base_path, name):
    return os.path.join(base_path, "QGIS 3.10", "bin", name)


def find_qgis():
    triedpaths = []
    for installpath in [qgis_path(os.environ['ProgramFiles'],"qgis-bin.exe"),
                        qgis_path(os.environ['ProgramFiles(x86)'], "qgis-bin.exe"),
                        qgis_path(os.environ['ProgramFiles'], "qgis-ltr-bin.exe"),
                        qgis_path(os.environ['ProgramFiles(x86)'], "qgis-ltr-bin.exe"),
                        ]:
        if os.path.exists(installpath):
            return installpath
        else:
            triedpaths.append(installpath)
    else:
        raise QGISNotFound(triedpaths)


def openqgis(project):
    """
    Open a session of QGIS and load the project. No plugins are loaded with the session.
    :param project:
    :return:
    """
    cmd = find_qgis()
    subprocess.Popen([cmd, "--noplugins", project])


def openfolder(folder):
    """
    Open a folder using the OS
    :param folder: The path to the folder to open.
    """
    QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


def render_tample(name, **data):
    template = env.get_template('{}.html'.format(name))
    return template.render(**data)

