from PyQt4.QtGui import QWidget

import roam.utils
import pprint

class WidgetBase(QWidget):
    def __init__(self, parent):
        super(WidgetBase, self).__init__(parent)
        self.project = None
        self.logger = roam.utils.logger
        self.config = None
        self.data = None
        self.roamapp = None

    def set_project(self, project, treenode):
        self.project = project
        self.treenode = treenode

    def unload_project(self):
        pass

    def write_config(self):
        """
        Write the config back to the project settings.
        """
        self.refresh()

    def refresh(self):
        pass

    def set_data(self, data):
        pprint.pprint(data)
        self.config = data['config']
        self.data = data
