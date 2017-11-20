import sys
import os
import subprocess
import roam.config

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QDesktopServices

from jinja2 import Environment, FileSystemLoader
from qgis.core import QGis

path = os.path.join(os.path.dirname(__file__), "templates", "html")

env = Environment(loader=FileSystemLoader(path))


def openqgis(project):
    """
    Open a session of QGIS and load the project. No plugins are loaded with the session.
    :param project:
    :return:
    """
    programfiles = os.environ["ProgramFiles"]
    programfilesW6432 = os.environ["ProgramW6432"]
    def checkpath(programfiles, version):
        qgispath = os.path.join(programfiles, version, "bin", "qgis.bat")
        return os.path.exists(qgispath), qgispath

    if "2.18" in QGis.QGIS_VERSION:
        # Try 32 bit first so we can match Roam version even though it doesn't really
        # matter
        found, path = checkpath(programfiles, "QGIS 2.16")
        if found:
            qgislocation = path
        else:
            found, path = checkpath(programfilesW6432, "QGIS 2.16")
            if found:
                qgislocation = path
    elif "2.18" in QGis.QGIS_VERSION:
        # Try 32 bit first so we can match Roam version even though it doesn't really
        # matter
        found, path = checkpath(programfiles, "QGIS 2.18")
        if found:
            qgislocation = path
        else:
            found, path = checkpath(programfilesW6432, "QGIS 2.18")
            if found:
                qgislocation = path
    else:
        qgislocation = r'C:\OSGeo4W\bin\qgis.bat'
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

