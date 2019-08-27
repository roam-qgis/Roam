import sys
import os
import subprocess
import roam.config

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from jinja2 import Environment, FileSystemLoader
from qgis.core import Qgis

path = os.path.join(os.path.dirname(__file__), "templates", "html")

env = Environment(loader=FileSystemLoader(path))


def openqgis(project):
    """
    Open a session of QGIS and load the project. No plugins are loaded with the session.
    :param project:
    :return:
    """
    osgeo4w = os.environ["OSGEO4W_ROOT"]
    name = os.environ["QGISNAME"]
    qgislocation = os.path.join(osgeo4w, "bin", "{}.bat".format(name))
    
    if not roam.config.settings.get("qgislocation", qgislocation) and os.path.exists(qgislocation):
        qgislocation = roam.config.settings.setdefault('configmanager', {}) \
            .setdefault('qgislocation', qgislocation)

    cmd = 'qgis'
    if sys.platform == 'win32':
        cmd = qgislocation
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

