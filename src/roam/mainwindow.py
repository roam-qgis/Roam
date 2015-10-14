from functools import partial
from collections import defaultdict
from subprocess import Popen
import getpass
import traceback
import os
import sys
import faulthandler


from PyQt4.QtCore import Qt, QFileInfo, QDir, QSize
from PyQt4.QtGui import (QActionGroup,
                        QApplication,
                        QWidget,
                        QSizePolicy,
                        QLabel,
                        QApplication,
                        QPixmap,
                        QColor,
                        QStandardItemModel,
                        QStandardItem,
                        QIcon,
                        QComboBox,
                        QAction,
                        QCursor, QFrame, QDesktopServices, QToolButton, QPushButton)
from qgis.core import (QgsProjectBadLayerHandler,
                        QgsPalLabeling,
                        QgsMapLayerRegistry,
                        QgsProject,
                        QgsMapLayer,
                        QgsFeature,
                        QgsFields,
                        QgsGeometry,
                        QgsRectangle,
                        QGis,
                        QgsApplication)
from qgis.gui import (QgsMessageBar,
                        QgsMapToolZoom,
                        QgsRubberBand,
                        QgsMapCanvas, QgsScaleComboBox)


from roam.popupdialogs import DeleteFeatureDialog
from roam.api.featureform import DeleteFeatureException
from roam.dataentrywidget import DataEntryWidget
from roam.listmodulesdialog import ProjectsWidget
from roam.settingswidget import SettingsWidget
from roam.project import Project, NoMapToolConfigured, ErrorInMapTool
from roam.infodock import InfoDock
from roam.syncwidget import SyncWidget
from roam.helpviewdialog import HelpPage
from roam.imageviewerwidget import ImageViewer
from roam.gpswidget import GPSWidget
from roam.updater import ProjectUpdater
from roam.api import RoamEvents, GPS, RoamInterface, plugins
from roam.ui import ui_mainwindow
from PyQt4.QtGui import QMainWindow
from roam.gpslogging import GPSLogging
from biglist import BigList


import roam.messagebaritems
import roam.utils
import roam.htmlviewer
import roam.api.featureform
import roam.config
import roam.defaults
import roam.api.utils
import roam.roam_style


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
        import roam
        self.projectwidget.project_base = roamapp.projectsroot

        QgsApplication.instance().setStyleSheet(roam.roam_style.appstyle())
        self.menutoolbar.setStyleSheet(roam.roam_style.menubarstyle())

        icon = roam.roam_style.iconsize()
        self.menutoolbar.setIconSize(QSize(icon, icon))

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
        self.actionLegend.triggered.connect(self.updatelegend)

        self.projectwidget.requestOpenProject.connect(self.loadProject)
        QgsProject.instance().readProject.connect(self._readProject)

        self.gpswidget.setgps(GPS)
        self.gpswidget.settracking(self.tracking)

        self.settings = {}
        self.actionSettings.toggled.connect(self.settingswidget.populateControls)
        self.actionSettings.toggled.connect(self.settingswidget.readSettings)
        self.settingswidget.settingsupdated.connect(self.settingsupdated)

        self.dataentrywidget = DataEntryWidget(self.canvas, self.bar)
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

        gpsspacewidget = createSpacer(30)
        sidespacewidget = createSpacer(30)
        sidespacewidget2 = createSpacer(height=20)

        sidespacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sidespacewidget2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.projectlabel = QLabel("Project: {project}")
        self.userlabel = QLabel("User: {user}".format(user=getpass.getuser()))
        self.positionlabel = QLabel('')
        self.gpslabel = QLabel("GPS: Not active")
        icon = QIcon(":/icons/info")
        infobutton = QToolButton()
        infobutton.setAutoRaise(True)
        infobutton.setMaximumHeight(self.statusbar.height())
        infobutton.setIcon(icon)
        # self.statusbar.addWidget(infobutton)
        self.snappingbutton = QToolButton()
        self.snappingbutton.setText("Snapping: On")
        self.snappingbutton.setAutoRaise(True)
        self.snappingbutton.pressed.connect(self.toggle_snapping)
        self.statusbar.addWidget(self.snappingbutton)
        # self.statusbar.addWidget(self.projectlabel)
        # self.statusbar.addWidget(self.userlabel)
        spacer = createSpacer()
        spacer2 = createSpacer()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.statusbar.addWidget(spacer)
        # self.statusbar.addWidget(self.positionlabel)
        self.statusbar.addWidget(spacer2)
        self.statusbar.addWidget(self.gpslabel)

        self.scalewidget = QgsScaleComboBox()

        self.scalebutton = QToolButton()
        self.scalebutton.setAutoRaise(True)
        self.scalebutton.setMaximumHeight(self.statusbar.height())
        self.scalebutton.pressed.connect(self.selectscale)
        self.scalebutton.setText("Scale")
        self.statusbar.addPermanentWidget(self.scalebutton)

        self.scalelist = BigList(parent=self.canvas, centeronparent=True, showsave=False)
        self.scalelist.hide()
        self.scalelist.setlabel("Map Scale")
        self.scalelist.setmodel(self.scalewidget.model())
        self.scalelist.closewidget.connect(self.scalelist.close)
        self.scalelist.itemselected.connect(self.update_scale_from_item)
        self.scalelist.itemselected.connect(self.scalelist.close)

        self.menutoolbar.insertWidget(self.actionQuit, sidespacewidget2)
        self.spaceraction = self.menutoolbar.insertWidget(self.actionProject, sidespacewidget)

        self.panels = []

        self.centralwidget.layout().addWidget(self.statusbar)

        self.actionGPSFeature.setProperty('dataentry', True)

        self.infodock = InfoDock(self.canvas)
        self.infodock.featureupdated.connect(self.highlightfeature)
        self.infodock.hide()
        self.hidedataentry()
        self.canvas.extentsChanged.connect(self.updatestatuslabel)
        self.canvas.scaleChanged.connect(self.updatestatuslabel)

        RoamEvents.openimage.connect(self.openimage)
        RoamEvents.openurl.connect(self.viewurl)
        RoamEvents.openfeatureform.connect(self.openForm)
        RoamEvents.openkeyboard.connect(self.openkeyboard)
        RoamEvents.editgeometry_complete.connect(self.on_geometryedit)
        RoamEvents.onShowMessage.connect(self.showUIMessage)
        RoamEvents.selectionchanged.connect(self.showInfoResults)
        RoamEvents.show_widget.connect(self.dataentrywidget.add_widget)
        RoamEvents.closeProject.connect(self.close_project)
        RoamEvents.snappingChanged.connect(self.snapping_changed)

        GPS.gpsposition.connect(self.update_gps_label)
        GPS.gpsdisconnected.connect(self.gps_disconnected)

        self.legendpage.showmap.connect(self.showmap)

        self.currentselection = {}

    def snapping_changed(self, snapping):
        if snapping:
            self.snappingbutton.setText("Snapping: On")
        else:
            self.snappingbutton.setText("Snapping: Off")
        
    def toggle_snapping(self):
        try:
            tool = self.canvas.mapTool()
            tool.toggle_snapping()
            snapping = tool.snapping
            self.snapping_changed(snapping)
        except AttributeError:
            pass

    def update_scale_from_item(self, index):
        scale, _ = self.scalewidget.toDouble(index.data(Qt.DisplayRole))
        self.canvas.zoomScale(1.0 / scale)

    def selectscale(self):
        self.scalelist.show()

    def set_projectbuttons(self, visible):
        for action in self.projectbuttons:
            action.setVisible(visible)

    def loadpages(self, pages):
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

            iface = RoamInterface(RoamEvents, GPS, self)
            pagewidget = PageClass(iface, self)

            safe_connect(RoamEvents.selectionchanged, pagewidget.selection_changed)
            safe_connect(RoamEvents.projectloaded, pagewidget.project_loaded)

            pageindex = self.stackedWidget.insertWidget(-1, pagewidget)
            action.setProperty('page', pageindex)
            self.pluginactions.append(action)
            self.menuGroup.addAction(action)

    def showUIMessage(self, label, message, level=QgsMessageBar.INFO, time=0, extra=''):
        self.bar.pushMessage(label, message, level, duration=time, extrainfo=extra)

    def updatelegend(self):
        self.legendpage.updatecanvas(self.canvas)

    def update_gps_label(self, position, gpsinfo):
        # Recenter map if we go outside of the 95% of the area
        self.gpslabel.setText("GPS: PDOP {0:.2f}   HDOP {1:.2f}    VDOP {2:.2f}".format(gpsinfo.pdop,
                                                                        gpsinfo.hdop,
                                                                        gpsinfo.vdop))

    def gps_disconnected(self):
        self.gpslabel.setText("GPS Not Active")

    def openkeyboard(self):
        if not roam.config.settings.get('keyboard', True):
            return

        roam.api.utils.open_keyboard()

    def viewurl(self, url):
        """
        Open a URL in Roam
        :param url:
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

    def openimage(self, pixmap):
        viewer = ImageViewer(self.stackedWidget)
        viewer.resize(self.stackedWidget.size())
        viewer.openimage(pixmap)

    def delete_feature(self, form, feature):
        """
        Delete the selected feature
        """
        # We have to make the feature form because the user might have setup logic
        # to handle the delete case

        featureform = form.create_featureform(feature)
        try:
            msg = featureform.deletemessage
        except AttributeError:
            msg = 'Do you really want to delete this feature?'

        if not DeleteFeatureDialog(msg).exec_():
            return

        try:
            featureform.delete()
        except DeleteFeatureException as ex:
            RoamEvents.raisemessage(*ex.error)

        featureform.featuredeleted(feature)
        self.show_undo("Feature deleted", "Undo Delete", form, feature)

    def show_undo(self, title, message, form, feature):
        item = roam.messagebaritems.UndoMessageItem(title, message, form, feature)
        item.undo.connect(self.undo_delete)
        self.bar.pushItem(item)

    def undo_delete(self, form, feature):
        # Add the feature back to the layer
        self.bar.popWidget()
        layer = form.QGISLayer
        layer.startEditing()
        layer.addFeature(feature)
        layer.commitChanges()

    def search_for_projects(self):
        server = roam.config.settings.get('updateserver', '')
        self.projectupdater.update_server(server, self.projects)

    def settingsupdated(self, settings):
        self.settings = settings
        self.show()
        self.canvas_page.settings_updated(settings)

    def updatestatuslabel(self, *args):
        extent = self.canvas.extent()
        self.positionlabel.setText("Map Center: {}".format(extent.center().toString()))
        scale = 1.0 / self.canvas.scale()
        scale = self.scalewidget.toString(scale)
        self.scalebutton.setText(scale)

    def on_geometryedit(self, form, feature):
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
        for selection_layer, features in self.currentselection.iteritems():
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
        info = traceback.format_exception(*exinfo)
        item = self.bar.pushError(QApplication.translate('MainWindowPy','Seems something has gone wrong. Press for more details', None, QApplication.UnicodeUTF8),
                                  info)



    def showhelp(self, parent, url):
        help = HelpPage(parent)
        help.setHelpPage(url)
        help.show()

    def dataentryfinished(self):
        self.hidedataentry()
        self.showmap()
        self.cleartempobjects()
        self.infodock.refreshcurrent()

    def featuresdeleted(self, layerid, featureids):
        layer = QgsMapLayerRegistry.instance().mapLayer(layerid)
        self.reloadselection(layer, deleted=featureids)
        self.canvas.refresh()

    def featureSaved(self, *args):
        #self.reloadselection(layer, deleted=[featureid])
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

    def exit(self):
        """
        Exit the application.
        """
        self.projectupdater.quit()
        self.close()

    def showInfoResults(self, results):
        forms = {}
        for layer in results.keys():
            layername = layer.name()
            if not layername in forms:
                forms[layername] = list(self.project.formsforlayer(layername))

        self.currentselection = results
        self.infodock.setResults(results, forms, self.project)
        self.infodock.show()


    def missingLayers(self, layers):
        """
        Called when layers have failed to load from the current project
        """
        roam.utils.warning("Missing layers")
        map(roam.utils.warning, layers)

        missinglayers = roam.messagebaritems.MissingLayerItem(layers,
                                                              parent=self.bar)
        self.bar.pushItem(missinglayers)

    def loadprojects(self, projects):
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

    def viewprojects(self):
        self.stackedWidget.setCurrentIndex(1)

    @roam.utils.timeit
    def _readProject(self, doc):
        """
        readProject is called by QgsProject once the map layer has been
        populated with all the layers
        """
        crs = self.canvas_page.init_qgisproject(doc)
        self.projectOpened()
        GPS.crs = crs

    @property
    def enabled_plugins(self):
        return self.settings.get('plugins', [])

    @roam.utils.timeit
    def projectOpened(self):
        """
            Called when a new project is opened in QGIS.
        """
        projectpath = QgsProject.instance().fileName()
        self.project = Project.from_folder(os.path.dirname(projectpath))
        self.projectlabel.setText("Project: {}".format(self.project.name))

        # Show panels
        for panel in self.project.getPanels():
            self.mainwindow.addDockWidget(Qt.BottomDockWidgetArea, panel)
            self.panels.append(panel)

        self.clear_plugins()
        self.add_plugins(self.project.enabled_plugins)

        layers = self.project.legendlayersmapping().values()
        self.legendpage.updateitems(layers)

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
        self.set_projectbuttons(True)
        self.dataentrywidget.project = self.project
        projectscales, _ = QgsProject.instance().readBoolEntry("Scales", "/useProjectScales")
        if projectscales:
            projectscales, _ = QgsProject.instance().readListEntry("Scales", "/ScalesList")

            self.scalewidget.updateScales(projectscales)
        else:
            scales = ["1:50000", "1:25000", "1:10000", "1:5000",
                      "1:2500", "1:1000", "1:500", "1:250", "1:200", "1:100"]
            scales = roam.config.settings.get('scales', scales)
            self.scalewidget.updateScales(scales)
        RoamEvents.projectloaded.emit(self.project)

    def clear_plugins(self):
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

    def add_plugins(self, pluginnames):
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
            self.loadpages(pages)

    @roam.utils.timeit
    def loadProject(self, project):
        """
        Load a project into the application .
        """
        roam.utils.log(project)
        roam.utils.log(project.name)
        roam.utils.log(project.projectfile)
        roam.utils.log(project.valid)

        (passed, message) = project.onProjectLoad()

        if not passed:
            self.bar.pushMessage("Project load rejected", "Sorry this project couldn't"
                                                          "be loaded.  Click for me details.",
                                 QgsMessageBar.WARNING, extrainfo=message)
            return

        self.actionMap.trigger()

        self.close_project()

        # No idea why we have to set this each time.  Maybe QGIS deletes it for
        # some reason.
        self.badLayerHandler = BadLayerHandler(callback=self.missingLayers)
        QgsProject.instance().setBadLayerHandler(self.badLayerHandler)

        # Project loading screen
        self.stackedWidget.setCurrentIndex(3)
        self.projectloading_label.setText("Project {} Loading".format(project.name))
        pixmap = QPixmap(project.splash)
        w = self.projectimage.width()
        h = self.projectimage.height()
        self.projectimage.setPixmap(pixmap.scaled(w,h, Qt.KeepAspectRatio))
        QApplication.processEvents()

        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        QgsProject.instance().read(fileinfo)

    def close_project(self, project=None):
        """
        Close the current open project
        """
        if not project is None and not project == self.project:
            return

        self.tracking.clear_logging()
        self.dataentrywidget.clear()
        self.canvas_page.cleanup()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        for panel in self.panels:
            self.removeDockWidget(panel)
            del panel
            # Remove all the old buttons

        self.panels = []
        oldproject = self.project
        self.project = None
        self.set_projectbuttons(False)
        self.hidedataentry()
        self.infodock.close()
        RoamEvents.selectioncleared.emit()
        RoamEvents.projectClosed.emit(oldproject)
        self.projectwidget.set_open_project(None)

