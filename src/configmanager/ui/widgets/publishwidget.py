import shutil
import os
import functools
import tempfile

from configmanager.ui.nodewidgets import ui_publishwidget
from configmanager.ui.widgets.widgetbase import WidgetBase
from configmanager.services.dataservice import DataService

from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QApplication, QFileDialog

import configmanager.bundle
import roam.project

from configmanager.utils import openfolder


def make_item(data, readonly=True):
    item = QTableWidgetItem(str(data))
    if readonly:
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
    return item


class PublishWidget(ui_publishwidget.Ui_widget, WidgetBase):
    def __init__(self, parent=None):
        super(PublishWidget, self).__init__(parent)
        self.setupUi(self)
        self.tableWidget.horizontalHeader().setResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(3, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(4, QHeaderView.ResizeToContents)
        self.publishProjectsButtons.pressed.connect(functools.partial(self.deploy_projects, False))
        self.publishProjectsAllButton.pressed.connect(functools.partial(self.deploy_projects, True))
        self.openFoldersButton.pressed.connect(self.open_folders)
        self.progressLabel.hide()
        self.filePickerButton.pressed.connect(self.pick_folder)
        self.updatePathsButton.pressed.connect(self.update_all_paths)
        self.projects = {}
        self.cache = {}
        self.dataservice = None

    def update_all_paths(self):
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 2)
            item.setText(self.deployLocationText.text())

    def pick_folder(self):
        path = QFileDialog().getExistingDirectory(self, "Select project publish location",
                                                  self.deployLocationText.text())
        self.deployLocationText.setText(path)

    def open_folders(self):
        projects = self.get_project_depoly_settings(all_projects=False).itervalues()
        for project in projects:
            openfolder(self.resolve_path(project['path']))

    def get_project_deploy_path(self, id):
        try:
            return self.config['projects'][id]['path']
        except KeyError:
            return r"C:\temp"

    def set_data(self, data):
        super(PublishWidget, self).set_data(data)
        self.dataservice = DataService(self.config)
        self.reload_projects()
        self.deployLocationText.setText(self.config.get('global_publish_path', ""))
        self.includeDataCheck.setChecked(self.config.get('include_data', True))
        self.refresh()

    def reload_projects(self):
        projects = list(roam.project.getProjects([self.data['projects_root']]))
        self.logger.debug(projects)
        self.projects = {}
        # Because we need a delete method anyway
        self.tableWidget.setRowCount(0)
        for rowno, project in enumerate(projects):
            self.tableWidget.insertRow(rowno)
            self.tableWidget.setItem(rowno, 0, make_item(project.id))
            self.tableWidget.setItem(rowno, 1, make_item(project.name))
            self.tableWidget.setItem(rowno, 2, make_item(self.get_project_deploy_path(project.id), readonly=False))
            self.tableWidget.setItem(rowno, 3, make_item(project.save_version))
            self.tableWidget.setItem(rowno, 4, make_item(project.version))
            self.projects[project.id] = project

    def write_config(self):
        self.logger.info("Saving publish config")
        projects = self.get_project_depoly_settings(True)
        self.config['global_publish_path'] = self.deployLocationText.text()
        self.config['projects'] = projects
        self.config['include_data'] = self.includeDataCheck.isChecked()
        self.config.save()
        super(PublishWidget, self).write_config()

    def refresh(self):
        pass

    def resolve_path(self, path):
        if not path:
            path = self.deployLocationText.text()
        if not path:
            path = os.path.join(self.roamapp.profileroot, "roam_serv")
        return path

    def deploy_projects(self, all_projects=False):
        self.write_config()

        self.progressLabel.show()

        datazipfile = None

        self.data_depolyed_folders = []
        for projectconfig in self.get_project_depoly_settings(all_projects=all_projects).itervalues():
            ## Gross but quicker then threading at the moment.
            QApplication.instance().processEvents()
            ## Fix the path to use the global location, or the roam_srv if that isn't set.
            projectconfig['path'] = self.resolve_path(projectconfig['path'])
            self.projects[projectconfig['id']].save(update_version=True, reset_save_point=True)
            if projectconfig['path'] not in self.data_depolyed_folders and self.includeDataCheck.isChecked():
                if not datazipfile:
                    datazipfile = self.make_zip()

                self.logger.info("DEPLOYYYY!!")
                self.logger.info("Deploying data for location {}".format(projectconfig['path']))
                self.deploy_data(projectconfig, datazipfile)
                self.data_depolyed_folders.append(projectconfig['path'])

            self.deploy_project(projectconfig)
            self.logger.info("Updating project.config")
        self.progressLabel.hide()
        self.reload_projects()

        self.write_config()

    def get_project_depoly_settings(self, all_projects):
        projects = {}
        seen = set()
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if not all_projects and not item.isSelected():
                continue
            id = self.tableWidget.item(row, 0).data(0)
            name = self.tableWidget.item(row, 1).data(0)
            path = self.tableWidget.item(row, 2).data(0)

            if name not in seen:
                projects[id] = {
                    "id": id,
                    "name": name,
                    "path": path
                }
        return projects

    def deploy_project(self, projectconfig):
        """
        Run the step to deploy a project. Projects are deplyed as a bundled zip of the project folder.
        """
        project = self.projects[projectconfig['id']]
        self.logger.info("Deploy {0} settings:".format(projectconfig['name']))
        self.logger.info("Deploy using settings:")
        self.logger.info(projectconfig)
        path = os.path.join(projectconfig['path'], "projects")

        if not os.path.exists(path):
            os.makedirs(path)

        # TODO Update project metadata
        options = {}

        configmanager.bundle.bundle_project(project, path, options, as_install=True)

    def make_zip(self):
        self.logger.info("ZIP IT. ZIP IT GOOD!")
        self.logger.info("Zipping data folder to temp folder")
        datazip = os.path.join(tempfile.gettempdir(), "_data.zip")
        configmanager.bundle.zipper(self.data['data_root'], "_data", datazip, {})
        return datazip

    def deploy_data(self, projectconfig, datazip):
        date = QDateTime.currentDateTimeUtc().toString(Qt.ISODate)

        path = os.path.join(projectconfig['path'], "projects")

        if not os.path.exists(path):
            os.makedirs(path)

        self.logger.info("Published config from: {}".format(path))
        publishedconfig = configmanager.bundle.get_config(path)

        shutil.copy(datazip, path)

        self.logger.info("Updating project data metadata")
        publishedconfig['data_date'] = date
        publishedconfig.save()
