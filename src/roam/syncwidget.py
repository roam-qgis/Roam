from functools import partial

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QAction, QSpacerItem, QSizePolicy

import roam.config
import roam.syncing
import roam.api.utils
from roam.api.events import RoamEvents
from roam.popupdialogs import ActionPickerWidget
from roam.ui.ui_sync import Ui_Form


class SyncWidget(Ui_Form, QWidget):
    syncqueue = []

    def __init__(self, parent=None):
        super(SyncWidget, self).__init__(parent)
        self.setupUi(self)
        roam.api.utils.install_touch_scroll(self.scrollArea)
        roam.api.utils.install_touch_scroll(self.syncstatus)
        self.syncrunning = False
        self.syncallButton.hide()

    def load_application_sync(self):
        print("Load application sync")
        providers = list(roam.syncing.syncprovders())
        if not providers:
            return

        actionwidget = ActionPickerWidget()
        actionwidget.setTile("Roam Syncing")
        for provider in providers:
            action = QAction(None)
            action.setText(provider.name)
            action.setIcon(QIcon(":/icons/sync"))
            action.triggered.connect(partial(self.run, action, provider))
            actionwidget.addAction(action)
        self.syncwidgets.layout().addWidget(actionwidget)

    def loadprojects(self, projects):
        # root = self.synctree.invisibleRootItem()
        self.load_application_sync()
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
        RoamEvents.sync_complete.emit()

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
