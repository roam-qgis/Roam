import functools
import os
import re
import zipfile
import urlparse
import urllib2
import Queue
import subprocess

from collections import defaultdict
from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt4.QtCore import QObject, pyqtSignal, QUrl, QThread


def checkversion(toversion, fromversion):
    def versiontuple(v):
        v = v.split('.')[:3]
        version = tuple(map(int, (v)))
        if len(version) == 2:
            version = (version[0], version[1], 0)
        return version

    return versiontuple(toversion) > versiontuple(fromversion)


def parse_serverprojects(content):
    reg = 'href="(?P<file>(?P<name>\w+)-(?P<version>\d+(\.\d+)+).zip)"'
    versions = defaultdict(dict)
    for match in re.finditer(reg, content, re.I):
        version = match.group("version")
        path = match.group("file")
        name = match.group("name")
        data = dict(path=path,
                    version=version,
                    name=name)
        versions[name][version] = data
    return dict(versions)


def update_project(project, version, serverurl):
    if not serverurl:
        raise ValueError("No server url given")

    filename = "{}-{}.zip".format(project.basefolder, version)
    url = urlparse.urljoin(serverurl, "projects/{}".format(filename))
    content = urllib2.urlopen(url).read()
    rootfolder = os.path.join(project.folder, "..")
    tempfolder = os.path.join(rootfolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    zippath = os.path.join(tempfolder, filename)
    yield "Running pre update scripts.."
    root = project.folder
    run_install_script(root, project.settings, "before_update")
    with open(zippath, "wb") as f:
        f.write(content)

    yield "Running update scripts.."
    run_install_script(root, project.settings, "after_update")

    yield "Installing"
    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(rootfolder)

    project.projectUpdated.emit(project)


def run_install_script(rootfolder, settings, section):
    try:
        os.chdir(rootfolder)
        commands = settings['install'][section]
        for command in commands:
            args = command.split()
            output = subprocess.check_output(args, shell=True)
            print output
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

