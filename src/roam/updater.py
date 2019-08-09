import yaml
import functools
import os
import re
import zipfile
import urlparse
import urllib
import urllib2
import Queue
import logging
import subprocess

import roam.utils

from collections import defaultdict
from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt4.QtCore import QObject, pyqtSignal, QUrl, QThread
from PyQt4.QtGui import QApplication

from qgis.core import QgsNetworkAccessManager

from roam.api import RoamEvents
import roam.project
import roam.config


class UpdateExpection(Exception):
    pass


def quote_url(url):
    return urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")


def add_slash(url):
    if not url.endswith("/"):
        url += "/"
    return url


def checkversion(toversion, fromversion):
    return int(toversion) > int(fromversion)


def parse_serverprojects(configdata):
    roam.utils.info("Project server data")
    roam.utils.info(configdata)
    if not configdata:
        return {}

    if isinstance(configdata, basestring):
        configdata = yaml.load(configdata)

    versions = defaultdict(dict)
    datadate = configdata.get('data_date', None)
    for project, data in configdata['projects'].iteritems():
        version = int(data["version"])
        path = project + ".zip"
        title = data['title']
        projectid = data.get('id', data['name'])
        name = project
        desc = data["description"]
        data = dict(path=path,
                    version=version,
                    name=name,
                    title=title,
                    description=desc,
                    projectid=projectid,
                    data_date=datadate)
        versions[project][version] = data
    return dict(versions)


def install_project(info, basefolder, serverurl, updateMode=False):
    if not serverurl:
        roam.utils.warning("No server url set for update")
        raise ValueError("No server url given")

    roam.utils.info("Downloading project zip")
    if updateMode:
        filename = "{}.zip".format(info['name'])
    else:
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
    project.projectUpdated.emit(project)


def download_file(url, fileout):
    """
    Download the file from the given URL and yield the status of the download

    Will open and write to fileout
    """
    url = quote_url(url)

    roam.utils.debug("Opening URL: {}".format(url))
    try:
        result = urllib2.urlopen(url)
    except urllib2.HTTPError as ex:
        if ex.code == 404:
            roam.utils.warning("Can't find URL: {}".format(url))
        else:
            roam.utils.exception("HTTP Error: {}".format(ex))
        yield "Error in download"
        raise UpdateExpection("Error in downloading file.")

    length = result.headers['content-length']

    length = int(length) / 1024 / 1024
    roam.utils.debug("Length: {}".format(length))
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
            yield info


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
        self.projectUpdateStatus.connect(self.status_updated)

    def check_url_found(self, url):
        url = quote_url(url)
        try:
            result = urllib2.urlopen(url)
            return result.code == 200
        except urllib2.HTTPError as ex:
            return False

    def fetch_data(self, rootfolder, filename, serverurl):
        """
        Download the update zip file for the project from the server
        """
        serverurl = add_slash(serverurl)

        tempfolder = os.path.join(rootfolder, "_updates")
        if not os.path.exists(tempfolder):
            os.mkdir(tempfolder)

        filename = "{}.zip".format(filename)
        url = urlparse.urljoin(serverurl, "projects/{}".format(filename))
        zippath = os.path.join(tempfolder, filename)
        if not self.check_url_found(url):
            yield "Skipping data download"
            yield "Done"
            return

        roam.utils.info("Downloading data zip from {}".format(url))
        try:
            for status in download_file(url, zippath):
                yield status
        except UpdateExpection as ex:
            roam.utils.exception("Error in update for project")
            yield "Error in downloading data"
            return

        yield "Extracting data.."
        with zipfile.ZipFile(zippath, "r") as z:
            members = z.infolist()
            for i, member in enumerate(members):
                z.extract(member, rootfolder)
                roam.utils.debug("Extracting: {}".format(member.filename))

        yield "Done"

    def status_updated(self, project, status):
        roam.utils.debug(project + ": " + status)

    def run(self):
        while True:
            project, version, server, is_new = forupdate.get()
            datadate = project["data_date"]
            datafolder = os.path.join(self.basefolder, "_data")
            if datadate != roam.config.settings.get("data_date", None) or not os.path.exists(datafolder):
                self.projectUpdateStatus.emit("Data", "Downloading Data..")
                for status in self.fetch_data(self.basefolder, "_data", server):
                    self.projectUpdateStatus.emit("Data", status)
                self.projectUpdateStatus.emit("Data", "Installed")
                roam.config.settings["data_date"] = datadate
                roam.config.save()
            else:
                roam.utils.info("Data download skipped. Already up to date.")

            if is_new:
                name = project['name']
                self.projectUpdateStatus.emit(name, "Installing")
                for status in install_project(project, self.basefolder, server):
                    self.projectUpdateStatus.emit(name, status)
                self.projectUpdateStatus.emit(name, "Installed")
                self.projectInstalled.emit(name)
            else:
                name = project['name']
                self.projectUpdateStatus.emit(name, "Updating")
                for status in install_project(project, self.basefolder, server, updateMode=True):
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
        print("URL", url)
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
            print(updateable)
            print(new)
            if updateable or new:
                self.foundProjects.emit(updateable, new)
        else:
            msg = "Error in network request for projects: {}".format(reply.errorString())
            roam.utils.warning(msg)

    def update_project(self, projectinfo):
        self.projectUpdateStatus.emit(projectinfo['name'], "Pending")
        forupdate.put((projectinfo, projectinfo['version'], self.server, False))
        self.updatethread.start()

    def install_project(self, projectinfo):
        self.projectUpdateStatus.emit(projectinfo['name'], "Pending")
        is_new = True
        forupdate.put((projectinfo, projectinfo['version'], self.server, is_new))
        self.updatethread.start()
