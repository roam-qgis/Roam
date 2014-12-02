from functools import partial

from PyQt4.QtGui import QIcon, QTreeWidgetItem, QPushButton, QWidget, QAction, QSpacerItem, QSizePolicy
from roam.api.events import RoamEvents

from ui.ui_sync import Ui_Form
from popupdialogs import ActionPickerWidget
from roam.flickwidget import FlickCharm



class SyncWidget(Ui_Form, QWidget):
    syncqueue = []
    def __init__(self, parent=None):
        super(SyncWidget, self).__init__(parent)
        self.setupUi(self)
        self.syncrunning = False
        self.syncallButton.hide()
        self.flickcharm = FlickCharm()
        self.flickcharm.activateOn(self.scrollArea)
        self.flickcharm.activateOn(self.syncstatus)

    def loadprojects(self, projects):
        #root = self.synctree.invisibleRootItem()
        for project in projects:
            providers = list(project.syncprovders())
            if not providers:
                continue

            actionwidget = ActionPickerWidget()
            actionwidget.setTile(project.name)
            for provider in providers:
                action = QAction(None)
                action.setText(provider.name)
                action.setIcon(QIcon(":/icons/sync"))
                action.triggered.connect(partial(self.run, action, provider))
                actionwidget.addAction(action)
            self.syncwidgets.layout().addWidget(actionwidget)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.syncwidgets.layout().addItem(spacerItem)

    def updatestatus(self, message):
        self.syncstatus.append(message)
        self.syncstatus.ensureCursorVisible()

    def updatewitherror(self, message):
        self.updatestatus('<b style="color:red">Error in sync: {}</b>'.format(message))
        self.updatestatus('')

    def updatecomplete(self):
        self.updatestatus('<b style="color:darkgreen">Sync complete</b>')
        self.updatestatus('')

    def runnext(self):
        try:
            provider = SyncWidget.syncqueue.pop(0)
            provider.syncComplete.connect(self.updatecomplete)
            provider.syncComplete.connect(self.runnext)
            provider.syncMessage.connect(self.updatestatus)
            provider.syncError.connect(self.updatewitherror)
            if provider.closeproject:
                RoamEvents.closeProject.emit(provider.project)
            provider.start()
        except IndexError:
            # If we get here we have run out of providers to run
            return

    def disconnect(self, provider):
        try:
            provider.syncComplete.disconnect()
            provider.syncMessage.disconnect()
            provider.syncStarted.disconnect()
            provider.syncError.disconnect()
        except TypeError:
            pass

    def syncfinished(self, action, provider):
        self.disconnect(provider)
        action.setText(provider.name)
        action.setEnabled(True)
        self.syncrunning = False

    def syncstarted(self, action, provider):
        self.updatestatus('<b style="font-size:large">Sync started for {}</h3>'.format(provider.name))
        action.setText('Running')
        action.setEnabled(False)
        self.syncrunning = True

    def run(self, action, provider):
        provider.syncStarted.connect(partial(self.syncstarted, action, provider))
        provider.syncFinished.connect(partial(self.syncfinished, action, provider))

        SyncWidget.syncqueue.append(provider)
        if self.syncrunning:
            action.setText("Pending")
        else:
            self.runnext()
