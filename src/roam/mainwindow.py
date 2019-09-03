import os
from functools import partial

from qgis.PyQt.QtCore import Qt, QDir, QSize, QUrl
from qgis.PyQt.QtGui import QPixmap, QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import (QActionGroup, QWidget, QSizePolicy, QApplication, QAction)
from qgis.PyQt.QtWidgets import QMainWindow
from qgis.core import (QgsProjectBadLayerHandler,
                       QgsProject,
                       QgsMapLayer,
                       Qgis,
                       QgsApplication)

import roam.api.featureform
import roam.api.utils
import roam.config
import roam.defaults
import roam.htmlviewer
import roam.messagebaritems
import roam.roam_style
import roam.utils
from roam.api import RoamEvents, GPS, RoamInterface, plugins
from roam.dataentrywidget import DataEntryWidget
from roam.gpslogging import GPSLogging
from roam.helpviewdialog import HelpPage
from roam.imageviewerwidget import ImageViewer
from roam.infodock import InfoDock
from roam.popupdialogs import DeleteFeatureDialog
from roam.project import Project
from roam.ui import ui_mainwindow
from roam.updater import ProjectUpdater


class BadLayerHandler(QgsProjectBadLayerHandler):
    """
    Handler class for any layers that fail to load when
    opening the project.
    """

    def __init__(self, callback):
        """
            callback - Any bad layers are passed to the callback so it
            can do what it wills with them
        """
        super(BadLayerHandler, self).__init__()
        self.callback = callback

    def handleBadLayers(self, domNodes, domDocument):
        layers = [node.namedItem("layername").toElement().text() for node in domNodes]
        self.callback(layers)


class MainWindow(ui_mainwindow.Ui_MainWindow, QMainWindow):
    """
    Main application window
    """

    def __init__(self, roamapp):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        import roam
        self.projectwidget.project_base = roamapp.projectsroot

        QgsApplication.instance().setStyleSheet(roam.roam_style.appstyle())
        self.menutoolbar.setStyleSheet(roam.roam_style.menubarstyle())

        icon = roam.roam_style.iconsize()
        self.menutoolbar.setIconSize(QSize(icon, icon))

        smallmode = roam.config.settings.get("smallmode", False)
        self.menutoolbar.setSmallMode(smallmode)

        self.projectupdater = ProjectUpdater(projects_base=roamapp.projectsroot)
        self.projectupdater.foundProjects.connect(self.projectwidget.show_new_updateable)
        self.projectupdater.projectUpdateStatus.connect(self.projectwidget.update_project_status)
        self.projectupdater.projectInstalled.connect(self.projectwidget.project_installed)
        self.projectwidget.search_for_updates.connect(self.search_for_projects)
        self.projectwidget.projectUpdate.connect(self.projectupdater.update_project)
        self.projectwidget.projectInstall.connect(self.projectupdater.install_project)
        self.project = None
        self.tracking = GPSLogging(GPS)

        self.canvas_page.set_gps(GPS, self.tracking)

        self.canvas = self.canvas_page.canvas
        # self.canvas_page.projecttoolbar.stateChanged.connect(self.menutoolbar.setSmallMode)
        # self.menutoolbar.stateChanged.connect(self.canvas_page.projecttoolbar.setSmallMode)

        roam.defaults.canvas = self.canvas
        self.bar = roam.messagebaritems.MessageBar(self.centralwidget)

        self.actionMap.setVisible(False)
        self.actionLegend.setVisible(False)

        self.menuGroup = QActionGroup(self)
        self.menuGroup.setExclusive(True)
        self.menuGroup.addAction(self.actionMap)
        self.menuGroup.addAction(self.actionDataEntry)
        self.menuGroup.addAction(self.actionLegend)
        self.menuGroup.addAction(self.actionProject)
        self.menuGroup.addAction(self.actionSync)
        self.menuGroup.addAction(self.actionSettings)
        self.menuGroup.addAction(self.actionGPS)
        self.menuGroup.triggered.connect(self.updatePage)

        self.projectbuttons = []
        self.pluginactions = []

        self.actionQuit.triggered.connect(self.exit)
        self.init_legend()

        self.projectwidget.requestOpenProject.connect(self.load_roam_project)
        QgsProject.instance().readProject.connect(self.project_opened)

        self.gpswidget.setgps(GPS)
        self.gpswidget.settracking(self.tracking)

        self.settings = {}
        self.actionSettings.toggled.connect(self.settingswidget.populateControls)
        self.actionSettings.toggled.connect(self.settingswidget.readSettings)
        self.settingswidget.settingsupdated.connect(self.settingsupdated)

        self.dataentrywidget = DataEntryWidget(self.canvas)
        self.dataentrywidget.lastwidgetremoved.connect(self.dataentryfinished)
        self.widgetpage.layout().addWidget(self.dataentrywidget)

        self.dataentrywidget.rejected.connect(self.formrejected)
        RoamEvents.featuresaved.connect(self.featureSaved)
        RoamEvents.helprequest.connect(self.showhelp)
        RoamEvents.deletefeature.connect(self.delete_feature)

        def createSpacer(width=0, height=0):
            widget = QWidget()
            widget.setMinimumWidth(width)
            widget.setMinimumHeight(height)
            return widget

        sidespacewidget = createSpacer(30)
        sidespacewidget2 = createSpacer(height=20)

        sidespacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sidespacewidget2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.menutoolbar.insertWidget(self.actionQuit, sidespacewidget2)
        self.spaceraction = self.menutoolbar.insertWidget(self.actionProject, sidespacewidget)

        self.panels = []

        self.actionGPSFeature.setProperty('dataentry', True)

        self.infodock = InfoDock(self.canvas)
        self.infodock.featureupdated.connect(self.highlightfeature)
        self.infodock.hide()
        self.hidedataentry()

        RoamEvents.openimage.connect(self.openimage)
        RoamEvents.openurl.connect(self.viewurl)
        RoamEvents.openfeatureform.connect(self.openForm)
        RoamEvents.openkeyboard.connect(self.openkeyboard)
        RoamEvents.editgeometry_complete.connect(self.on_geometryedit)
        RoamEvents.onShowMessage.connect(self.show_ui_message)
        RoamEvents.selectionchanged.connect(self.show_info_results)
        RoamEvents.show_widget.connect(self.dataentrywidget.add_widget)
        RoamEvents.closeProject.connect(self.close_project)

        self.legendpage.showmap.connect(self.showmap)

        self.currentselection = {}

        iface = RoamInterface(RoamEvents, GPS, self, self.canvas_page, self)
        plugins.api = iface

    def delete_feature(self, form, feature) -> None:
        """
        Slot called when a feature needs to be deleted.
        :param form: The form to use when deleting the feature.
        :param feature: The feature to delete.
        """
        featureform = form.create_featureform(feature)

        try:
            msg = featureform.deletemessage
        except AttributeError:
            msg = 'Do you really want to delete this feature?'

        box = DeleteFeatureDialog(msg)

        if not box.exec_():
            return

        try:
            featureform.delete()
        except featureform.DeleteFeatureException as ex:
            RoamEvents.raisemessage(*ex.error)
            return

        featureform.featuredeleted(feature)

    def show_project_menu_buttons(self, visible: bool) -> None:
        """
        Show/Hide the the project side menu buttons.
        :param visible: The visible state for the menu buttons.
        """
        for action in self.projectbuttons:
            action.setVisible(visible)

    def add_plugin_pages(self, pages) -> None:
        """
        Add pages from the plugin to the side pabel.
        :param pages: List of plugin page classes to create and attach to the side panel.
        """

        def safe_connect(method, to):
            try:
                method.connect(to)
            except AttributeError:
                pass

        for PageClass in pages:
            action = QAction(self.menutoolbar)
            text = PageClass.title.ljust(13)
            action.setIconText(text)
            action.setIcon(QIcon(PageClass.icon))
            action.setCheckable(True)
            if PageClass.projectpage:
                action.setVisible(False)
                self.projectbuttons.append(action)
                self.menutoolbar.insertAction(self.spaceraction, action)
            else:
                self.menutoolbar.insertAction(self.actionProject, action)

            pagewidget = PageClass(plugins.api, self)

            safe_connect(RoamEvents.selectionchanged, pagewidget.selection_changed)
            safe_connect(RoamEvents.projectloaded, pagewidget.project_loaded)

            pageindex = self.stackedWidget.insertWidget(-1, pagewidget)
            action.setProperty('page', pageindex)
            self.pluginactions.append(action)
            self.menuGroup.addAction(action)

    def show_ui_message(self, label, message, level=Qgis.Info, time=0, extra='') -> None:
        """
        Show a message to the user in the message bar.
        :param label: The label used as the message header.
        :param message: The main message.
        :param level: The level of the message. Default Qgis.Info
        :param time: The length of time in seconds to show the message.
        :param extra: An extra data to show the user.
        :return:
        """
        self.bar.pushMessage(label, message, level, duration=time, extrainfo=extra)

    def init_legend(self) -> None:
        """
        Init the legend object with the canvas.
        :return:
        """
        self.legendpage.init(self.canvas)

    def openkeyboard(self) -> None:
        """
        Open the on screen keyboard
        :return:
        """
        if not roam.config.settings.get('keyboard', True):
            return

        # TODO Use the Qt keyboard
        roam.api.utils.open_keyboard()

    def viewurl(self, url: QUrl) -> None:
        """
        Open a URL in Roam
        :param url: The URL to view. bb
        :return:
        """
        key = url.toString().lstrip('file://')
        try:
            # Hack. Eww fix me.
            data, imagetype = roam.htmlviewer.images[os.path.basename(key)]
            pix = QPixmap()
            if imagetype == 'base64':
                pix.loadFromData(data)
            else:
                pix.load(data)
            self.openimage(pix)
        except KeyError:
            pix = QPixmap()
            pix.load(key)
            if pix.isNull():
                QDesktopServices.openUrl(url)
                return
            self.openimage(pix)

    def openimage(self, pixmap: QPixmap) -> None:
        """
        Open the image viewer for the given pixmap
        :param pixmap: The pixmap to open in the viewer
        """
        viewer = ImageViewer(self.stackedWidget)
        viewer.resize(self.stackedWidget.size())
        viewer.openimage(pixmap)

    def show_undo(self, title, message, form, feature):
        item = roam.messagebaritems.UndoMessageItem(title, message, form, feature)
        item.undo.connect(self.undo_delete)
        self.bar.pushItem(item)

    def undo_delete(self, form, feature) -> None:
        """
        Undo a delete of a feature.
        :param form:
        :param feature:
        :return:
        """
        # Add the feature back to the layer
        self.bar.popWidget()
        layer = form.QGISLayer
        layer.startEditing()
        layer.addFeature(feature)
        layer.commitChanges()

    def search_for_projects(self) -> None:
        """
        Search for plugins from the update server.
        """
        server = roam.config.settings.get('updateserver', '')
        self.projectupdater.update_server(server, self.projects)

    def settingsupdated(self, settings) -> None:
        """
        Called when the settings have been updated. Used to keep the UI in sync with any settings
        changes.
        :param settings: The new settings.
        """
        self.settings = settings
        self.show()
        smallmode = self.settings.get("smallmode", False)
        self.menutoolbar.setSmallMode(smallmode)
        self.canvas_page.settings_updated(settings)

    def on_geometryedit(self, form, feature) -> None:
        """
        Called when a features geometry has been edited.
        :param form: The form to pull the QGIS layer from.
        :param feature: The feature that had it's geometry updated.
        """
        layer = form.QGISLayer
        self.reloadselection(layer, updated=[feature])

    def handle_removed_features(self, layer, layerid, deleted_feature_ids):
        self.canvas.refresh()
        self.reloadselection(layer, deleted=deleted_feature_ids)

    def reloadselection(self, layer, deleted=[], updated=[]):
        """
        Reload the selection after features have been updated or deleted.
        :param layer:
        :param deleted:
        :param updated:
        :return:
        """
        selectedfeatures = []
        for selection_layer, features in self.currentselection.items():
            if layer.name() == selection_layer.name():
                selectedfeatures = features
                layer = selection_layer
                break

        if not selectedfeatures:
            return

        # Update any features that have changed.
        for updatedfeature in updated:
            oldfeatures = [f for f in selectedfeatures if f.id() == updatedfeature.id()]
            for feature in oldfeatures:
                self.currentselection[layer].remove(feature)
                self.currentselection[layer].append(updatedfeature)

        # Delete any old ones
        for deletedid in deleted:
            oldfeatures = [f for f in selectedfeatures if f.id() == deletedid]
            for feature in oldfeatures:
                self.currentselection[layer].remove(feature)

        RoamEvents.selectionchanged.emit(self.currentselection)

    def highlightfeature(self, layer, feature, features):
        self.canvas_page.highlight_active_selection(layer, feature, features)
        RoamEvents.activeselectionchanged.emit(layer, feature, features)

    def showmap(self):
        self.actionMap.setVisible(True)
        self.actionLegend.setVisible(True)
        self.actionMap.trigger()

    def hidedataentry(self):
        self.actionDataEntry.setVisible(False)

    def showdataentry(self):
        self.actionDataEntry.setVisible(True)
        self.actionDataEntry.trigger()

    def raiseerror(self, *exinfo):
        info = self.bar.pushError(*exinfo)
        # import roam.errors
        # errors.send_exception(exinfo)

    def showhelp(self, parent, url):
        """
        Show the help page in the UI.
        :param parent:
        :param url:
        :return:
        """
        help = HelpPage(parent)
        help.setHelpPage(url)
        help.show()

    def dataentryfinished(self):
        self.hidedataentry()
        self.showmap()
        self.cleartempobjects()
        self.infodock.refreshcurrent()

    def featuresdeleted(self, layerid, featureids):
        layer = QgsProject.instance().mapLayer(layerid)
        self.reloadselection(layer, deleted=featureids)
        self.canvas.refresh()

    def featureSaved(self, *args):
        # self.reloadselection(layer, deleted=[featureid])
        self.canvas.refresh()

    def cleartempobjects(self):
        self.canvas_page.clear_temp_objects()

    def formrejected(self, message, level):
        if message:
            RoamEvents.raisemessage("Form Message", message, level, duration=2)

    def openForm(self, form, feature, editmode, *args):
        """
        Open the form that is assigned to the layer
        """
        self.showdataentry()
        self.dataentrywidget.load_feature_form(feature, form, editmode, *args)

    def editfeaturegeometry(self, form, feature, newgeometry):
        layer = form.QGISLayer
        layer.startEditing()
        feature.setGeometry(newgeometry)
        layer.updateFeature(feature)
        saved = layer.commitChanges()
        map(roam.utils.error, layer.commitErrors())
        self.canvas.refresh()
        RoamEvents.editgeometry_complete.emit(form, feature)

    def exit(self) -> None:
        """
        Exit the application.
        """
        self.close()

    def show_info_results(self, results) -> None:
        """
        Show the info panel with the given results
        :param results: The results to show in the info panel.
        """
        forms = {}
        for layer in results.keys():
            layername = layer.name()
            if not layername in forms:
                forms[layername] = list(self.project.formsforlayer(layername))

        self.currentselection = results
        self.infodock.setResults(results, forms, self.project)
        self.infodock.show()

    def missing_layers_handler(self, layers):
        """
        Called when layers have failed to load from the current project
        """
        roam.utils.warning("Missing layers")
        map(roam.utils.warning, layers)
        missinglayers = roam.messagebaritems.MissingLayerItem(layers)
        self.bar.pushItem(missinglayers)

    def load_projects(self, projects):
        """
        Load the given projects into the project
        list
        """
        projects = list(projects)
        self.projects = projects
        self.projectwidget.loadProjectList(projects)
        self.syncwidget.loadprojects(projects)
        self.search_for_projects()

    def updatePage(self, action):
        """
        Update the current stack page based on the current selected
        action
        """
        page = action.property("page")
        self.stackedWidget.setCurrentIndex(page)

    def show(self):
        """
        Override show method. Handles showing the app in fullscreen
        mode or just maximized
        """
        fullscreen = roam.config.settings.get("fullscreen", False)
        if fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()

    def show_project_list(self):
        """
        Show the project list as the current page in the app.
        :return:
        """
        self.stackedWidget.setCurrentIndex(1)

    @property
    def enabled_plugins(self) -> list:
        """
        Return the names of the enabled plugins
        :return: List of plugin names that should be enabled.
        """
        return self.settings.get('plugins', [])

    @roam.utils.timeit
    def project_opened(self, doc):
        """
        Called when a new project is opened in QGIS.
        :param: doc The project document that was opened in QGIS.
        """
        GPS.crs = self.canvas_page.crs
        projectpath = QgsProject.instance().fileName()
        self.project = Project.from_folder(os.path.dirname(projectpath))

        # Show panels
        try:
            ## TODO Port this logic or drop in Roam 3
            for panel in self.project.getPanels():
                self.mainwindow.addDockWidget(Qt.BottomDockWidgetArea, panel)
                self.panels.append(panel)
        except NotImplementedError:
            pass


        self.clear_plugins()
        self.add_plugins(self.project.enabled_plugins)

        layers = self.project.legendlayersmapping().values()
        self.legendpage.setRoot(QgsProject.instance().layerTreeRoot())

        gps_loglayer = self.project.gpslog_layer()
        if gps_loglayer:
            self.tracking.enable_logging_on(gps_loglayer)
        else:
            roam.utils.info("No gps_log found for GPS logging")
            self.tracking.clear_logging()

        for layer in roam.api.utils.layers():
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue
            layer.committedFeaturesRemoved.connect(partial(self.handle_removed_features, layer))

        self.canvas_page.project_loaded(self.project)
        self.showmap()
        self.show_project_menu_buttons(True)
        self.dataentrywidget.project = self.project
        RoamEvents.projectloaded.emit(self.project)

    def clear_plugins(self) -> None:
        """
        Clear the loaded plugins.
        """
        self.projectbuttons = []
        self.projectbuttons.append(self.actionMap)
        self.projectbuttons.append(self.actionLegend)
        for action in self.pluginactions:
            # Remove the page widget, because we make it on each load
            widget = self.stackedWidget.widget(action.property("page"))
            self.stackedWidget.removeWidget(widget)
            if widget:
                widget.deleteLater()

            self.menutoolbar.removeAction(action)
        self.pluginactions = []

    def add_plugins(self, pluginnames) -> None:
        """
        Add loaded plugins panels to the main interface.
        :param pluginnames: The names of the plugins to load into the interface
        :return:
        """
        for name in pluginnames:
            # Get the plugin
            try:
                plugin_mod = plugins.loaded_plugins[name]
            except KeyError:
                continue

            if not hasattr(plugin_mod, 'pages'):
                roam.utils.warning("No pages() function found in {}".format(name))
                continue

            pages = plugin_mod.pages()
            self.add_plugin_pages(pages)

    @roam.utils.timeit
    def load_roam_project(self, project):
        """
        Load a project into the application.
        """
        roam.utils.log(project)
        roam.utils.log(project.name)
        roam.utils.log(project.projectfile)
        roam.utils.log(project.valid)

        (passed, message) = project.onProjectLoad()

        if not passed:
            self.bar.pushMessage("Project load rejected", "Sorry this project couldn't"
                                                          "be loaded.  Click for me details.",
                                 Qgis.Warning, extrainfo=message)
            return

        self.actionMap.trigger()

        self.close_project()

        # No idea why we have to set this each time.  Maybe QGIS deletes it for
        # some reason.
        self.badLayerHandler = BadLayerHandler(callback=self.missing_layers_handler)
        QgsProject.instance().setBadLayerHandler(self.badLayerHandler)

        # Project loading screen
        self.stackedWidget.setCurrentIndex(3)
        self.projectloading_label.setText("Project {} Loading".format(project.name))
        pixmap = QPixmap(project.splash)
        w = self.projectimage.width()
        h = self.projectimage.height()
        self.projectimage.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))
        QApplication.processEvents()

        QDir.setCurrent(os.path.dirname(project.projectfile))
        project.load_project()

    def close_project(self, project=None):
        """
        Close the current open project
        """
        if project is not None and not project == self.project:
            return

        RoamEvents.projectClosing.emit()
        self.tracking.clear_logging()
        self.dataentrywidget.clear()
        self.canvas_page.cleanup()
        QgsProject.instance().removeAllMapLayers()
        for panel in self.panels:
            self.removeDockWidget(panel)
            del panel
            # Remove all the old buttons

        self.panels = []
        oldproject = self.project
        self.project = None
        self.show_project_menu_buttons(False)
        self.hidedataentry()
        self.infodock.close()
        RoamEvents.selectioncleared.emit()
        RoamEvents.projectClosed.emit(oldproject)
        self.projectwidget.set_open_project(None)
