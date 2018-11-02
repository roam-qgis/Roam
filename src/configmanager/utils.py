import sys
import os
import subprocess
import roam.config

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QDesktopServices

from jinja2 import Environment, FileSystemLoader
from qgis.core import QGis

from roam.utils import error

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
    def checkpath(programfiles, version, name="qgis"):
        qgispath = os.path.join(programfiles, version, "bin", "{}.bat".format(name))
        return os.path.exists(qgispath), qgispath

    qgislocation = roam.config.settings.setdefault('configmanager', {}).get('qgislocation', None)
    if not qgislocation:
        if "2.18" in QGis.QGIS_VERSION:
            # Try 32 bit first so we can match Roam version even though it doesn't really
            # matter
            found, path = checkpath(programfiles, "QGIS 2.18", "qgis-ltr")
            if found:
                qgislocation = path
            else:
                found, path = checkpath(programfilesW6432, "QGIS 2.18", "qgis-ltr")
                if found:
                    qgislocation = path
            roam.config.settings.setdefault('configmanager', {})['qgislocation'] = qgislocation
        else:
            raise Exception("Unable to find install of QGIS 2.18")

    cmd = 'qgis'
    if sys.platform == 'win32':
        cmd = qgislocation
    print(cmd)
    try:
        subprocess.Popen([cmd, "--noplugins", project])
    except OSError as ex:
        error("Error opening QGIS: {}".format(str(ex)))
        raise



def openfolder(folder):
    """
    Open a folder using the OS
    :param folder: The path to the folder to open.
    """
    QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


def render_tample(name, **data):
    template = env.get_template('{}.html'.format(name))
    return template.render(**data)

