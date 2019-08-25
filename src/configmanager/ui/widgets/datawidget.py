import re
import os

from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QDateTime, Qt

from qgis.core import QgsProviderRegistry

from configmanager.ui.nodewidgets import ui_datawidget
from configmanager.ui.widgets.widgetbase import WidgetBase
from configmanager.utils import openfolder
from configmanager.services.dataservice import DataService


class DataWidget(ui_datawidget.Ui_widget, WidgetBase):
    def __init__(self, parent=None):
        super(DataWidget, self).__init__(parent)
        self.setupUi(self)
        self.model = QFileSystemModel()
        self.settings = None
        allfilters = []
        filters = re.findall(r"\((.*?)\)", QgsProviderRegistry.instance().fileVectorFilters())[1:]
        for filter in filters:
            allfilters = allfilters + filter.split(" ")

        filters += re.findall(r"\((.*?)\)", QgsProviderRegistry.instance().fileRasterFilters())[1:]
        for filter in filters:
            allfilters = allfilters + filter.split(" ")
        self.model.setNameFilters(allfilters)
        self.model.setNameFilterDisables(False)
        self.listDataList.setModel(self.model)
        self.btnAddData.pressed.connect(self.open_data_folder)
        for col in range(self.model.columnCount())[1:]:
            self.listDataList.hideColumn(col)
        self.service = None

    def open_data_folder(self):
        """
        Open the data folder of the project using the OS
        """
        path = os.path.join(self.data['data_root'])
        openfolder(path)

    def set_data(self, data):
        super(DataWidget, self).set_data(data)
        self.service = DataService(self.config)

        root = data['data_root']

        if not os.path.exists(root):
            os.mkdir(root)
        self.model.setRootPath(root)
        self.listDataList.setRootIndex(self.model.index(root))
        self.refresh()

    def write_config(self):
        self.logger.info("Data write config")
        DataService(self.config).update_date_to_latest()
        super(DataWidget, self).write_config()

    def refresh(self):
        self.lastSaveLabel.setText("Last save date: {}".format(self.service.last_save_date))
