import yaml
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

import roam.project


def checkversion(toversion, fromversion):
    return int(toversion) > int(fromversion)


def parse_serverprojects(configdata):
    if isinstance(configdata, basestring):
        configdata = yaml.load(configdata)

    versions = defaultdict(dict)
    for project, data in configdata['projects'].iteritems():
        version = int(data["version"])
        path = project + ".zip"
        title = data['title']
        name = project
        desc = data["description"]
        data = dict(path=path,
                    version=version,
                    name=name,
                    title=title)
        versions[project][version] = data
    return dict(versions)


def install_project(info, basefolder, serverurl):
    if not serverurl:
        roam.utils.warning("No server url set for update")
        raise ValueError("No server url given")

    roam.utils.info("Downloading project zip")
    filename = "{}.zip".format(info['name'])
    url = urlparse.urljoin(serverurl, "projects/{}".format(filename))
    content = urllib2.urlopen(url).read()
    tempfolder = os.path.join(basefolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    zippath = os.path.join(tempfolder, filename)
    with open(zippath, "wb") as f:
        f.write(content)

    yield "Installing"
    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(basefolder)

    project = roam.project.Project.from_folder(os.path.join(basefolder, info['name']))

    os.chdir(project.folder)
    yield "Running update scripts.."
    run_install_script(project.settings, "after_update")


def update_project(project, version, serverurl):
    if not serverurl:
        roam.utils.warning("No server url set for update")
        raise ValueError("No server url given")

    roam.utils.info("Downloading project zip")
    filename = "{}.zip".format(project.basefolder)
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

    yield "Installing"
    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(rootfolder)

    os.chdir(project.folder)
    yield "Running update scripts.."
    run_install_script(project.settings, "after_update")

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


def new_projects(projects, serverprojects):
    names = [project.basefolder for project in projects]
    for projectname, versions in serverprojects.iteritems():
        if projectname not in names:
            info = get_project_info(projectname, serverprojects)
            yield info


forupdate = Queue.Queue()


class UpdateWorker(QObject):
    projectUpdateStatus = pyqtSignal(str, str)
    projectInstalled = pyqtSignal(str)

    def __init__(self, basefolder):
        super(UpdateWorker, self).__init__()
        self.server = None
        self.basefolder = basefolder

    def run(self):
        while True:
            project, version, server, is_new = forupdate.get()
            if is_new:
                name = project['name']
                self.projectUpdateStatus.emit(name, "Installing")
                for status in install_project(project, self.basefolder, server):
                    self.projectUpdateStatus.emit(name, status)
                self.projectUpdateStatus.emit(name, "Installed")
                self.projectInstalled.emit(name)
            else:
                name = project.name
                self.projectUpdateStatus.emit(name, "Updating")
                for status in update_project(project, version, server):
                    self.projectUpdateStatus.emit(name, status)
                self.projectUpdateStatus.emit(name, "Complete")


class ProjectUpdater(QObject):
    """
    Object to handle reporting when new versions of projects are found on the update server.

    Emits foundProjects when a new projects are found
    """
    foundProjects = pyqtSignal(list, list)
    projectUpdateStatus = pyqtSignal(str, str)
    projectInstalled = pyqtSignal(str)

    def __init__(self, server=None, projects_base=''):
        super(ProjectUpdater, self).__init__()
        self.server = server
        self.net = QNetworkAccessManager()
        self.projects_base = projects_base
        self.create_worker()

    def create_worker(self):
        self.updatethread = QThread()
        self.worker = UpdateWorker(self.projects_base)
        self.worker.moveToThread(self.updatethread)

        self.worker.projectUpdateStatus.connect(self.projectUpdateStatus)
        self.worker.projectInstalled.connect(self.projectInstalled)
        self.updatethread.started.connect(self.worker.run)

    @property
    def configurl(self):
        url = urlparse.urljoin(self.server, "projects/roam.txt")
        return url

    def check_updates(self, server, installedprojects):
        if not server:
            return

        self.server = server
        req = QNetworkRequest(QUrl(self.configurl))
        reply = self.net.get(req)
        reply.finished.connect(functools.partial(self.list_versions, reply, installedprojects))

    def update_server(self, newserverurl, installedprojects):
        self.check_updates(newserverurl, installedprojects)

    def list_versions(self, reply, installedprojects):
        content = reply.readAll().data()
        print content
        serverversions = parse_serverprojects(content)
        updateable = list(updateable_projects(installedprojects, serverversions))
        new = list(new_projects(installedprojects, serverversions))
        if updateable or new:
            self.foundProjects.emit(updateable, new)

    def update_project(self, project, version):
        self.projectUpdateStatus.emit(project.name, "Pending")
        forupdate.put((project, version, self.server, False))
        self.updatethread.start()

    def install_project(self, projectinfo):
        self.projectUpdateStatus.emit(projectinfo['name'], "Pending")
        is_new = True
        forupdate.put((projectinfo, projectinfo['version'], self.server, is_new))
        self.updatethread.start()

