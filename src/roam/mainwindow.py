from functools import partial
from collections import defaultdict
from subprocess import Popen
import getpass
import traceback
import os
import sys


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
                        QgsRectangle, QGis)
from qgis.gui import (QgsMessageBar,
                        QgsMapToolZoom,
                        QgsRubberBand,
                        QgsMapCanvas)


from roam.dataentrywidget import DataEntryWidget
from roam.listmodulesdialog import ProjectsWidget
from roam.settingswidget import SettingsWidget
from roam.projectparser import ProjectParser
from roam.project import Project, NoMapToolConfigured, ErrorInMapTool
from roam.infodock import InfoDock
from roam.syncwidget import SyncWidget
from roam.helpviewdialog import HelpPage
from roam.biglist import BigList
from roam.imageviewerwidget import ImageViewer
from roam.gpswidget import GPSWidget
from roam.api import RoamEvents, GPS
from roam.ui import ui_mainwindow
from PyQt4.QtGui import QMainWindow
from roam.gpslogging import GPSLogging


import roam.messagebaritems
import roam.utils
import roam.htmlviewer
import roam.api.featureform
import roam.config
import roam.defaults
import roam.api.utils


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

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.canvaslayers = []
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

        self.actionQuit.triggered.connect(self.exit)
        self.actionLegend.triggered.connect(self.updatelegend)

        self.projectwidget.requestOpenProject.connect(self.loadProject)
        QgsProject.instance().readProject.connect(self._readProject)

        self.gpswidget.setgps(GPS)
        self.gpswidget.settracking(self.tracking)

        self.actionSettings.toggled.connect(self.settingswidget.populateControls)
        self.actionSettings.toggled.connect(self.settingswidget.readSettings)
        self.settingswidget.settingsupdated.connect(self.settingsupdated)

        self.dataentrywidget = DataEntryWidget(self.canvas, self.bar)
        self.widgetpage.layout().addWidget(self.dataentrywidget)

        self.dataentrywidget.rejected.connect(self.formrejected)
        self.dataentrywidget.featuresaved.connect(self.featureSaved)
        self.dataentrywidget.featuredeleted.connect(self.featuredeleted)
        self.dataentrywidget.failedsave.connect(self.failSave)
        self.dataentrywidget.helprequest.connect(self.showhelp)

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

        def createlabel(text):
            style = """
                QLabel {
                        color: #706565;
                        font: 14px "Calibri" ;
                        }"""
            label = QLabel(text)
            label.setStyleSheet(style)

            return label

        self.projectlabel = createlabel("Project: {project}")
        self.userlabel = createlabel("User: {user}".format(user=getpass.getuser()))
        self.positionlabel = createlabel('')
        self.gpslabel = createlabel("GPS: Not active")
        self.statusbar.addWidget(self.projectlabel)
        self.statusbar.addWidget(self.userlabel)
        spacer = createSpacer()
        spacer2 = createSpacer()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.statusbar.addWidget(spacer)
        self.statusbar.addWidget(self.positionlabel)
        self.statusbar.addWidget(spacer2)
        self.statusbar.addWidget(self.gpslabel)

        self.menutoolbar.insertWidget(self.actionQuit, sidespacewidget2)
        self.menutoolbar.insertWidget(self.actionProject, sidespacewidget)

        self.panels = []

        self.centralwidget.layout().addWidget(self.statusbar)

        self.actionGPSFeature.setProperty('dataentry', True)

        self.infodock = InfoDock(self.canvas)
        self.infodock.featureupdated.connect(self.highlightfeature)
        self.infodock.hide()
        self.hidedataentry()
        self.canvas.extentsChanged.connect(self.updatestatuslabel)

        RoamEvents.openimage.connect(self.openimage)
        RoamEvents.openurl.connect(self.viewurl)
        RoamEvents.openfeatureform.connect(self.openForm)
        RoamEvents.openkeyboard.connect(self.openkeyboard)
        RoamEvents.editgeometry_complete.connect(self.on_geometryedit)
        RoamEvents.onShowMessage.connect(self.showUIMessage)
        RoamEvents.selectionchanged.connect(self.showInfoResults)
        RoamEvents.featureformloaded.connect(self.featureformloaded)

        GPS.gpsposition.connect(self.update_gps_label)
        GPS.gpsdisconnected.connect(self.gps_disconnected)

        self.legendpage.showmap.connect(self.showmap)

        self.currentselection = {}

    def showUIMessage(self, label, message, level=QgsMessageBar.INFO, time=0, extra=''):
        self.bar.pushMessage(label, message, level, duration=time, extrainfo=extra)

    def updatelegend(self):
        self.legendpage.updatecanvas(self.canvas)

    def update_gps_label(self, position, gpsinfo):
        # Recenter map if we go outside of the 95% of the area
        self.gpslabel.setText("GPS: PDOP {}   HDOP {}    VDOP {}".format(gpsinfo.pdop,
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

    def settingsupdated(self, settings):
        self.show()
        self.canvas_page.settings_updated(settings)

    def updatestatuslabel(self):
        extent = self.canvas.extent()
        self.positionlabel.setText("Map Center: {}".format(extent.center().toString()))

    def on_geometryedit(self, form, feature):
        layer = form.QGISLayer
        self.reloadselection(layer, updated=[feature])

    def reloadselection(self, layer, deleted=[], updated=[]):
        """
        Reload the selection after features have been updated or deleted.
        :param layer:
        :param deleted:
        :param updated:
        :return:
        """
        selectedfeatures = self.currentselection[layer]

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



    def showhelp(self, url):
        help = HelpPage(self.stackedWidget)
        help.setHelpPage(url)
        help.show()

    def dataentryfinished(self):
        self.hidedataentry()
        self.showmap()
        self.cleartempobjects()
        self.infodock.refreshcurrent()

    def featuredeleted(self, layer, featureid):
        self.dataentryfinished()
        self.reloadselection(layer, deleted=[featureid])
        self.canvas.refresh()

    def featureSaved(self):
        self.dataentryfinished()
        self.canvas.refresh()

    def failSave(self, messages):
        self.bar.pushError("Error when saving changes.", messages)

    def cleartempobjects(self):
        self.canvas_page.clear_temp_objects()

    def formrejected(self, message, level):
        self.dataentryfinished()
        if message:
            RoamEvents.raisemessage("Form Message", message, level, duration=2)

        self.cleartempobjects()

    def featureformloaded(self, form, feature, project, editmode):
        self.showdataentry()

    def openForm(self, form, feature, editmode):
        """
        Open the form that is assigned to the layer
        """
        self.dataentrywidget.openform(feature=feature, form=form, project=self.project, editmode=editmode)

    def exit(self):
        """
        Exit the application.
        """
        QApplication.exit(0)

    def showInfoResults(self, results):
        forms = {}
        for layer in results.keys():
            layername = layer.name()
            if not layername in forms:
                forms[layername] = list(self.project.formsforlayer(layername))

        self.currentselection = results
        self.infodock.setResults(results, forms)
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
        self.projectwidget.loadProjectList(projects)
        self.syncwidget.loadprojects(projects)

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
        parser = ProjectParser(doc)
        canvasnode = parser.canvasnode
        self.canvas.freeze()
        self.canvas.mapRenderer().readXML(canvasnode)
        self.canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(self.canvaslayers)
        #red = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorRedPart", 255 )[0];
        #green = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorGreenPart", 255 )[0];
        #blue = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorBluePart", 255 )[0];
        #color = QColor(red, green, blue);
        #self.canvas.setCanvasColor(color)
        self.canvas.updateScale()
        self.projectOpened()
        self.canvas.freeze(False)
        self.canvas.refresh()
        GPS.crs = self.canvas.mapRenderer().destinationCrs()
        self.showmap()

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

        layers = self.project.legendlayersmapping().values()
        self.legendpage.updateitems(layers)

        try:
            gps_loglayer = QgsMapLayerRegistry.instance().mapLayersByName('gps_log')[0]
            if roam.config.settings.get('gpslogging', True):
                self.tracking.enable_logging_on(gps_loglayer)
        except IndexError:
            roam.utils.info("No gps_log found for GPS logging")
            self.tracking.clear_logging()

        self.canvas_page.projectloaded(self.project)

    #noinspection PyArgumentList
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

        self.closeProject()

        self.canvas.refresh()
        self.canvas.repaint()

        RoamEvents.selectioncleared.emit()

        # No idea why we have to set this each time.  Maybe QGIS deletes it for
        # some reason.
        self.badLayerHandler = BadLayerHandler(callback=self.missingLayers)
        QgsProject.instance().setBadLayerHandler(self.badLayerHandler)

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

    def closeProject(self):
        """
        Close the current open project
        """
        self.tracking.clear_logging()
        self.dataentrywidget.clear()
        self.canvas_page.cleanup()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        for panel in self.panels:
            self.removeDockWidget(panel)
            del panel
            # Remove all the old buttons

        self.panels = []
        self.project = None
        self.hidedataentry()
        self.infodock.close()



