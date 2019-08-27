from PyQt5.QtWidgets import QWidget

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
        self.closing = False

    def set_project(self, project, treenode):
        self.project = project
        self.treenode = treenode

    def unload_project(self):
        self.logger.debug("Unload for widget {}".format(self.__class__.__name__))

    def on_closing(self):
        self.logger.debug("On close for widget {}".format(self.__class__.__name__))
        self.closing = True

    def write_config(self):
        """
        Write the config back to the project settings.
        """
        self.logger.debug("Write config for widget {}".format(self.__class__.__name__))
        if not self.closing:
            # Only refresh the widget if we are not closing.
            self.refresh()

    def refresh(self):
        if self.closing:
            return

    def set_data(self, data):
        pprint.pprint(data)
        self.config = data['config']
        self.data = data
