import functools
import os
import re
import zipfile
import urlparse
import urllib2
import Queue
import logging
import subprocess

import roam.utils

from collections import defaultdict
from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt4.QtCore import QObject, pyqtSignal, QUrl, QThread


def checkversion(toversion, fromversion):
    return int(toversion) > int(fromversion)


def parse_serverprojects(content):
    reg = '(?P<file>(?P<name>\w+)-(?P<version>\d+).zip)'
    versions = defaultdict(dict)
    for match in re.finditer(reg, content, re.I):
        version = int(match.group("version"))
        path = match.group("file")
        name = match.group("name")
        data = dict(path=path,
                    version=version,
                    name=name)
        versions[name][version] = data
    return dict(versions)


def update_project(project, version, serverurl):
    if not serverurl:
        roam.utils.warning("No server url set for update")
        raise ValueError("No server url given")

    roam.utils.info("Downloading project zip")
    filename = "{}-{}.zip".format(project.basefolder, version)
    url = urlparse.urljoin(serverurl, "projects/{}".format(filename))
    content = urllib2.urlopen(url).read()
    rootfolder = os.path.join(project.folder, "..")
    tempfolder = os.path.join(rootfolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    os.chdir(project.folder)
    yield "Running pre update scripts.."
    run_install_script(project.settings, "before_update")
    zippath = os.path.join(tempfolder, filename)
    with open(zippath, "wb") as f:
        f.write(content)

    os.chdir(project.folder)
    yield "Running update scripts.."
    run_install_script(project.settings, "after_update")

    yield "Installing"
    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(rootfolder)

    project.projectUpdated.emit(project)


def run_install_script(settings, section):
    try:
        commands = settings['install'][section]
        for command in commands:
            roam.utils.info("Running command: {}".format(command))
            args = command.split()
            if args[0].lower() == 'cd':
                os.chdir(args[1])
            else:
                output = subprocess.check_output(args, shell=True)
                roam.utils.info(output)
    except KeyError:
        pass


def get_project_info(projectname, projects):
    maxversion = max(projects[projectname])
    projectdata = projects[projectname][maxversion]
    return projectdata


def can_update(projectname, currentversion, projects):
    try:
        maxversion = max(projects[projectname])
        return checkversion(maxversion, currentversion)
    except KeyError:
        return False
    except ValueError:
        return False


def updateable_projects(projects, serverprojects):
    for project in projects:
        canupdate = can_update(project.basefolder, project.version, serverprojects)
        if canupdate:
            info = get_project_info(project.basefolder, serverprojects)
            yield project, info


forupdate = Queue.Queue()


class UpdateWorker(QObject):
    projectUpdateStatus = pyqtSignal(object, str)

    def __init__(self):
        super(UpdateWorker, self).__init__()
        self.server = None

    def run(self):
        while True:
            project, version, server = forupdate.get()
            self.projectUpdateStatus.emit(project, "Updating")
            for status in update_project(project, version, server):
                self.projectUpdateStatus.emit(project, status)
            self.projectUpdateStatus.emit(project, "complete")


class ProjectUpdater(QObject):
    """
    Object to handle reporting when new versions of projects are found on the update server.

    Emits foundProjects when a new projects are found
    """
    foundProjects = pyqtSignal(object)
    projectUpdateStatus = pyqtSignal(object, str)

    def __init__(self, server=None):
        super(ProjectUpdater, self).__init__()
        self.server = server
        self.net = QNetworkAccessManager()
        self.worker()

    def worker(self):
        self.updatethread = QThread()
        self.worker = UpdateWorker()
        self.worker.moveToThread(self.updatethread)

        self.worker.projectUpdateStatus.connect(self.projectUpdateStatus)
        self.updatethread.started.connect(self.worker.run)

    @property
    def projecturl(self):
        url = urlparse.urljoin(self.server, "projects/")
        return url

    def check_updates(self, server, installedprojects):
        if not server:
            return

        self.server = server
        req = QNetworkRequest(QUrl(self.projecturl))
        reply = self.net.get(req)
        reply.finished.connect(functools.partial(self.list_versions, reply, installedprojects))

    def update_server(self, newserverurl, installedprojects):
        self.check_updates(newserverurl, installedprojects)

    def list_versions(self, reply, installedprojects):
        content = reply.readAll().data()
        serverversions = parse_serverprojects(content)
        updateable = list(updateable_projects(installedprojects, serverversions))
        if updateable:
            self.foundProjects.emit(updateable)

    def update_project(self, project, version):
        self.projectUpdateStatus.emit(project, "Pending")
        forupdate.put((project, version, self.server))
        self.updatethread.start()

