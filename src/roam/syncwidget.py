from functools import partial

from PyQt4.QtGui import QIcon, QTreeWidgetItem, QPushButton, QWidget

from ui.ui_sync import Ui_Form
from roam.flickwidget import FlickCharm

class SyncWidget(Ui_Form, QWidget):
    syncqueue = []
    def __init__(self, parent=None):
        super(SyncWidget, self).__init__(parent)
        self.setupUi(self)
        self.syncrunning = False
        self.syncallButton.hide()
        self.flickcharm = FlickCharm()
        self.flickcharm.activateOn(self.synctree)
        self.flickcharm.activateOn(self.syncstatus)

    def loadprojects(self, projects):
        root = self.synctree.invisibleRootItem()
        for project in projects:
            providers = list(project.syncprovders())
            if not providers:
                continue

            projectitem = QTreeWidgetItem(root)
            projectitem.setText(0, project.name)
            projectitem.setIcon(0, QIcon(project.splash))
            for provider in providers:
                provideritem = QTreeWidgetItem(projectitem)
                provideritem.setText(0, provider.name)
                button = QPushButton()
                button.pressed.connect(partial(self.run, button, provider))
                button.setText(provider.name)
                self.synctree.setItemWidget(provideritem,0, button)

        self.synctree.expandAll()

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

    def syncfinished(self, button, provider):
        self.disconnect(provider)
        button.setText(provider.name)
        button.setEnabled(True)
        self.syncrunning = False

    def syncstarted(self, button, provider):
        self.updatestatus('<b style="font-size:large">Sync started for {}</h3>'.format(provider.name))
        button.setText('Running')
        button.setEnabled(False)
        self.syncrunning = True

    def run(self, button, provider):
        provider.syncStarted.connect(partial(self.syncstarted, button, provider))
        provider.syncFinished.connect(partial(self.syncfinished, button, provider))

        SyncWidget.syncqueue.append(provider)
        if self.syncrunning:
            button.setText("Pending")
        else:
            self.runnext()
