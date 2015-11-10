import sys
import os
import subprocess
import roam.config

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QDesktopServices

from jinja2 import Environment, FileSystemLoader
path = os.path.join(os.path.dirname(__file__), "templates", "html")

env = Environment(loader=FileSystemLoader(path))


def openqgis(project):
    """
    Open a session of QGIS and load the project. No plugins are loaded with the session.
    :param project:
    :return:
    """
    qgislocation = r'C:\OSGeo4W\bin\qgis.bat'
    qgislocation = roam.config.settings.setdefault('configmanager', {}) \
        .setdefault('qgislocation', qgislocation)
    cmd = 'qgis'
    if sys.platform == 'win32':
        cmd = qgislocation
    subprocess.Popen([cmd, "--noplugins", project])


def render_tample(name, **data):
    template = env.get_template('{}.html'.format(name))
    return template.render(**data)


def openfolder(folder):
    """
    Open a folder using the OS
    :param folder: The path to the folder to open.
    """
    QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


