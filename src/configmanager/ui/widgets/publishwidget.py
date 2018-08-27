import shutil
import os
import functools
import tempfile

from configmanager.ui.nodewidgets import ui_publishwidget
from configmanager.ui.widgets.widgetbase import WidgetBase
from configmanager.services.dataservice import DataService

from PyQt4.QtGui import QTableWidgetItem, QHeaderView, QApplication, QFileDialog

import configmanager.bundle
import roam.project

from configmanager.utils import openfolder


def make_item(data):
    return QTableWidgetItem(str(data))


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
        self.filePickerButton.pressed.connect(self.pick_folder)
        self.updatePathsButton.pressed.connect(self.update_all_paths)
        self.progressBar.hide()
        self.projects = {}
        self.cache = {}

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
            openfolder(project['path'])

    def get_project_deploy_path(self, id):
        try:
            return self.config['projects'][id]['path']
        except KeyError:
            return r"C:\temp"

    def set_data(self, data):
        super(PublishWidget, self).set_data(data)
        self.reload_projects()

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
            self.tableWidget.setItem(rowno, 2, make_item(self.get_project_deploy_path(project.id)))
            self.tableWidget.setItem(rowno, 3, make_item(project.save_version))
            self.tableWidget.setItem(rowno, 4, make_item(project.version))
            self.projects[project.id] = project

    def write_config(self):
        self.logger.info("Saving publish config")
        projects = self.get_project_depoly_settings(True)
        self.config['projects'] = projects
        self.config.save()

    def deploy_projects(self, all_projects=False):
        self.write_config()

        self.progressBar.show()
        dataoptions = {
            "data_date": DataService(self.config).read()['data_save_date']
        }
        for projectconfig in self.get_project_depoly_settings(all_projects=all_projects).itervalues():
            ## Gross but quicker then threading at the moment.
            QApplication.instance().processEvents()
            ## Save first to bump to version up.
            self.projects[projectconfig['id']].save(update_version=True, reset_save_point=True)
            self.deploy_data(projectconfig, dataoptions)
            self.deploy_project(projectconfig)
            self.logger.info("Updating project.config")
        self.progressBar.hide()
        self.reload_projects()

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

    def deploy_data(self, projectconfig, dataoptions):
        def make_zip():
            self.logger.info("Zipping data folder to temp folder")
            datazip = os.path.join(tempfile.gettempdir(), "_data.zip")
            configmanager.bundle.zipper(self.data['data_root'], "_data", datazip, {})
            self.cache["data_zip"] = datazip
            self.cache["data_date"] = datadate
            return datazip

        path = os.path.join(projectconfig['path'], "projects")

        if not os.path.exists(path):
            os.makedirs(path)

        self.logger.info("Published config from: {}".format(path))
        publishedconfig = configmanager.bundle.get_config(path)

        publihseddatadata = publishedconfig.get('data_date', None)
        datadate = dataoptions.get('data_date', None)
        if datadate is None:
            DataService(self.config).update_date_to_latest()

        if publihseddatadata != datadate:
            self.logger.info(
                "Updating _data.zip file to latest data. Publish date {} vs {}".format(publihseddatadata, datadate))

            if self.cache.get('data_date', None) == datadate and "data_zip" in self.cache:
                datazip = self.cache['data_zip']
                self.logger.info("Got data zip path from cache {}".format(datazip))
            else:
                datazip = make_zip()

            shutil.copy(datazip, path)

            self.logger.info("Updating project data metadata")
            publishedconfig['data_date'] = datadate
            publishedconfig.save()
        else:
            self.logger.info("Data already on latest version")
