from PyQt4.QtGui import QDialog

from configmanager.ui import ui_configmanager


class ConfigManagerDialog(ui_configmanager.Ui_ProjectInstallerDialog, QDialog):
    def __init__(self, parent=None):
        super(ConfigManagerDialog, self).__init__(parent)
        self.setupUi(self)
