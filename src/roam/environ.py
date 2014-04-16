import os
import sys

from qgis.core import QgsApplication, QgsProviderRegistry

from PyQt4.QtGui import QApplication, QFont, QImageReader, QImageWriter
from PyQt4.QtCore import QLocale, QTranslator
import PyQt4.QtSql


class RoamApp(object):
    def __init__(self, sysargv, apppath, prefixpath, settingspath, libspath, i18npath):
        self.sysargv = sysargv
        self.apppath = apppath
        self.prefixpath = prefixpath
        self.settingspath = settingspath
        self.libspath = libspath
        self.i18npath = i18npath
        self.app = None
        self.translationFile = None

    def init(self):
        self.app = QgsApplication(self.sysargv, True)
        QgsApplication.setPrefixPath(self.prefixpath, True)
        QgsApplication.initQgis()

        locale = QLocale.system().name()
        self.translationFile = os.path.join(self.i18npath, '{0}.qm'.format(locale))
        translator = QTranslator()
        translator.load(self.translationFile, "i18n")
        self.app.installTranslator(translator)

        QApplication.setStyle("Plastique")
        QApplication.setFont(QFont('Segoe UI'))
        return self

    def exec_(self):
        self.app.exec_()

    def exit(self):
        sys.exit()

    def setActiveWindow(self, widget):
        self.app.setActiveWindow(widget)

    def dump_configinfo(self):
        yield QgsProviderRegistry.instance().pluginList()
        yield QImageReader.supportedImageFormats()
        yield QImageWriter.supportedImageFormats()
        yield QgsApplication.libraryPaths()
        yield "Translation file: {}".format(self.translationFile)


def setup(argv):
    """
    Setup the environment for Roam.

    Returns the QGIS prefix path and settings path.
    """
    frozen = getattr(sys, "frozen", False)
    RUNNING_FROM_FILE = not frozen
    apppath = os.path.dirname(os.path.realpath(argv[0]))
    prefixpath = os.path.join(apppath, "libs", "qgis")
    libspath = os.path.join(apppath, "libs", "roam")
    i18npath = os.path.join(libspath, "i18n")
    settingspath = os.path.join(apppath, "settings.config")

    # Set the PATH and GDAL_DRIVER_PATH for gdal to find the plugins.
    # Not sure why we have to set these here but GDAL doesn't like it if we
    # don't
    os.environ['PATH'] += ";{}".format(os.path.join(apppath, 'libs'))
    os.environ['PATH'] += ";{}".format(apppath)
    os.environ["GDAL_DRIVER_PATH"] = os.path.join(apppath, 'libs')
    os.environ["GDAL_DATA"] = os.path.join(apppath, 'libs', 'gdal')

    if RUNNING_FROM_FILE:
        print "Running from file"
        # Setup the paths for OSGeo4w if we are running from a file
        # this means that we are not running from a frozen app.
        os.environ['PATH'] += r";C:\OSGeo4W\bin;C:\OSGeo4W\apps\qgis\bin"
        sys.path.append(r"C:\OSGeo4W\apps\qgis\python")
        os.environ["GDAL_DATA"] = r"C:\OSGeo4W\share\gdal"
        os.environ["GDAL_DRIVER_PATH"] = r"C:\OSGeo4W\bin\gdalplugins"
        os.environ["QT_PLUGIN_PATH"] = r"C:\OSGeo4W\apps\Qt4\plugins"
        libspath = os.path.join(apppath)
        i18npath = os.path.join(libspath, "i18n")
        prefixpath = os.environ['QGIS_PREFIX_PATH']


    return RoamApp(argv, apppath, prefixpath, settingspath, libspath, i18npath).init()


def projectpaths(argv, settings={}):
    # Add the default paths
    paths = []
    try:
        paths.append(argv[1])
    except IndexError:
        paths.append(os.path.join(os.getcwd(), "projects"))
    paths.extend(settings.get('projectpaths', []))
    sys.path.extend(paths)
    return paths
