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
from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt4.QtCore import QObject, pyqtSignal, QUrl, QThread

from qgis.core import QgsNetworkAccessManager

from roam.api import  RoamEvents
import roam.project


def add_slash(url):
    if not url.endswith("/"):
        url += "/"
    return url


def checkversion(toversion, fromversion):
    return int(toversion) > int(fromversion)


def parse_serverprojects(configdata):
    if not configdata:
        return {}

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
                    title=title,
                    description=desc)
        versions[project][version] = data
    return dict(versions)


def install_project(info, basefolder, serverurl):
    if not serverurl:
        roam.utils.warning("No server url set for update")
        raise ValueError("No server url given")

    roam.utils.info("Downloading project zip")
    filename = "{}-Install.zip".format(info['name'])
    serverurl = add_slash(serverurl)
    url = urlparse.urljoin(serverurl, "projects/{}".format(filename))

    tempfolder = os.path.join(basefolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    zippath = os.path.join(tempfolder, filename)
    for status in download_file(url, zippath):
        yield status

    yield "Installing"
    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(basefolder)

    project = roam.project.Project.from_folder(os.path.join(basefolder, info['name']))

    os.chdir(project.folder)
    yield "Running update scripts.."
    run_install_script(project.settings, "after_update")

    # Update the project after install because it might be out of date.
    for status in update_project(project, serverurl):
        yield status


def download_file(url, fileout):
    """
    Download the file from the given URL and yield the status of the download

    Will open and write to fileout
    """
    result = urllib2.urlopen(url)
    length = result.headers['content-length']

    length = int(length) / 1024 / 1024
    yield "Downloading 0/{}MB".format(length)
    bytes_done = 0
    with open(fileout, "wb") as f:
        chunk = 4096
        while True:
            data = result.read(chunk)
            if not data:
                yield "Download complete"
                break

            bytes_done += len(data)
            f.write(data)
            so_far = bytes_done / 1024 / 1024
            yield "Downloading {}/{}MB".format(so_far, length)


def update_project(project, serverurl):
    """
    Download the update zip file for the project from the server
    """
    if not serverurl:
        roam.utils.warning("No server url set for update")
        raise ValueError("No server url given")

    roam.utils.info("Downloading project zip")
    serverurl = add_slash(serverurl)

    rootfolder = os.path.join(project.folder, "..")
    tempfolder = os.path.join(rootfolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    os.chdir(project.folder)
    yield "Running pre update scripts.."
    run_install_script(project.settings, "before_update")

    filename = "{}.zip".format(project.basefolder)
    url = urlparse.urljoin(serverurl, "projects/{}".format(filename))
    zippath = os.path.join(tempfolder, filename)
    for status in download_file(url, zippath):
        yield status

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
                for status in update_project(project, server):
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
        self.updatethread = None
        self.server = server
        self.net = QgsNetworkAccessManager.instance()
        self.projects_base = projects_base
        self.create_worker()

    def quit(self):
        self.updatethread.quit()

    def create_worker(self):
        self.updatethread = QThread()
        self.worker = UpdateWorker(self.projects_base)
        self.worker.moveToThread(self.updatethread)

        self.worker.projectUpdateStatus.connect(self.projectUpdateStatus)
        self.worker.projectInstalled.connect(self.projectInstalled)
        self.updatethread.started.connect(self.worker.run)

    @property
    def configurl(self):
        url = urlparse.urljoin(add_slash(self.server), "projects/roam.txt")
        print "URL", url
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
        if reply.error() == QNetworkReply.NoError:
            content = reply.readAll().data()
            serverversions = parse_serverprojects(content)
            updateable = list(updateable_projects(installedprojects, serverversions))
            new = list(new_projects(installedprojects, serverversions))
            if updateable or new:
                self.foundProjects.emit(updateable, new)
        else:
            msg = "Error in network request for projects: {}".format(reply.errorString())
            roam.utils.warning(msg)
            RoamEvents.raisemessage("Project Server Message", msg, level=RoamEvents.WARNING)

    def update_project(self, project, version):
        self.projectUpdateStatus.emit(project.name, "Pending")
        forupdate.put((project, version, self.server, False))
        self.updatethread.start()

    def install_project(self, projectinfo):
        self.projectUpdateStatus.emit(projectinfo['name'], "Pending")
        is_new = True
        forupdate.put((projectinfo, projectinfo['version'], self.server, is_new))
        self.updatethread.start()

