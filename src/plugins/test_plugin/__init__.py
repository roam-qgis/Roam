from PyQt4.QtGui import QWidget, QGridLayout, QLabel, QIcon

from roam.api import plugins

__author__ = 'Test User'
__description__ = "Report plugin to generate simple reports in the field"

@plugins.page(name='TestPlugin', title='Test', icon=QIcon(r'report_icon.svg'), projectpage=True)
class ReportPage(QWidget):
    def __init__(self, api, parent=None):
        super(ReportPage, self).__init__(parent)
        self.api = api
        self.setLayout(QGridLayout())
        self.label = QLabel()
        self.layout().addWidget(self.label)
        api.events.RoamEvents.selectionchanged.connect(self.selection_updated)

    def selection_updated(self, selection):
        text = ''
        for layer in selection.iterkeys():
            print layer.name()
            text += layer.name() + '\n'
        self.label.setText(text)
