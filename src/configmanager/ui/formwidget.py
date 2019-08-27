__author__ = 'Nathan.Woodrow'

from qgis.PyQt.QtWidgets import QWidget

from configmanager.ui.ui_formwidget import Ui_FormWidget

class FormWidget(Ui_FormWidget, QWidget):
    def __init__(self, parent=None):
        super(FormWidget, self).__init__(parent)
        self.setupUi(self)
