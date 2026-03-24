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


def qgis_bin_path(base_path, folder_name, exe_name):
    return os.path.join(base_path, folder_name, "bin", exe_name)


def find_qgis():
    triedpaths = []

    # 1. Allow explicit override first
    for env_var in ["QGIS_BIN", "QGIS_EXECUTABLE"]:
        env_path = os.environ.get(env_var)
        if env_path:
            if os.path.exists(env_path):
                return env_path
            triedpaths.append(env_path)

    # 2. OSGeo4W common locations
    osgeo_roots = [
        r"C:\OSGeo4W",
        r"C:\OSGeo4W64",
        r"C:\Program Files\OSGeo4W",
    ]

    for root in osgeo_roots:
        for exe_name in ["qgis-ltr-bin.exe", "qgis-bin.exe"]:
            installpath = os.path.join(root, "bin", exe_name)
            if os.path.exists(installpath):
                return installpath
            triedpaths.append(installpath)

    # 3. Standard standalone QGIS installs
    program_files_roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
    ]

    qgis_folders = [
        "QGIS",
        "QGIS 3.10",
        "QGIS 3.16",
        "QGIS 3.22",
        "QGIS 3.28",
        "QGIS 3.34",
        "QGIS 3.40",
    ]

    for base_path in program_files_roots:
        if not base_path:
            continue

        for folder_name in qgis_folders:
            for exe_name in ["qgis-ltr-bin.exe", "qgis-bin.exe"]:
                installpath = qgis_bin_path(base_path, folder_name, exe_name)
                if os.path.exists(installpath):
                    return installpath
                triedpaths.append(installpath)

    # 4. Fall back to PATH lookup
    for exe_name in ["qgis-ltr-bin.exe", "qgis-bin.exe"]:
        try:
            result = subprocess.run(
                ["where", exe_name],
                capture_output=True,
                text=True,
                check=False,
                shell=True,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    candidate = line.strip()
                    if not candidate:
                        continue
                    if os.path.exists(candidate):
                        return candidate
                    triedpaths.append(candidate)
        except Exception:
            pass

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

