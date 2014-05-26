import os
import sys



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
        from qgis.core import QgsApplication
        from PyQt4.QtGui import QApplication, QFont
        from PyQt4.QtCore import QLocale, QTranslator
        try:
            import PyQt4.QtSql
        except ImportError:
            pass

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
        from qgis.core import QgsApplication
        QgsApplication.exitQgis()
        QgsApplication.quit()

    def setActiveWindow(self, widget):
        self.app.setActiveWindow(widget)

    def dump_configinfo(self):
        from qgis.core import QgsApplication, QgsProviderRegistry
        from PyQt4.QtGui import QImageReader, QImageWriter
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
    try:
        # Added so we can test the packaged version of Roam using the unit tests.
        apppath = os.environ['ROAM_APPPATH']
        print apppath
        RUNNING_FROM_FILE = False
    except KeyError:
        apppath = os.path.dirname(os.path.realpath(argv[0]))

    prefixpath = os.path.join(apppath, "libs", "qgis")
    libspath = os.path.join(apppath, "libs", "roam")
    i18npath = os.path.join(libspath, "i18n")
    settingspath = os.path.join(apppath, "roam.config")
    if not os.path.exists(settingspath):
        settingspath = os.path.join(apppath, "settings.config")

    if RUNNING_FROM_FILE:
        print "Running from file"
        libspath = os.path.join(apppath, "roam")
        i18npath = os.path.join(apppath, "i18n")
        prefixpath = os.environ['QGIS_PREFIX_PATH']
    else:
        # Set the PATH and GDAL_DRIVER_PATH for gdal to find the plugins.
        # Not sure why we have to set these here but GDAL doesn't like it if we
        # don't
        os.environ['PATH'] += ";{}".format(os.path.join(apppath, 'libs'))
        os.environ['PATH'] += ";{}".format(apppath)
        os.environ["GDAL_DRIVER_PATH"] = os.path.join(apppath, 'libs')
        os.environ["GDAL_DATA"] = os.path.join(apppath, 'libs', 'gdal')

    return RoamApp(argv, apppath, prefixpath, settingspath, libspath, i18npath).init()


def projectpaths(argv, roamapp, settings={}):
    # Add the default paths
    paths = []
    try:
        paths.append(argv[1])
    except IndexError:
        paths.append(os.path.join(roamapp.apppath, "projects"))

    paths.extend(settings.get('projectpaths', []))
    for path in paths:
        rootfolder = os.path.abspath(os.path.join(path, '..'))
        sys.path.append(rootfolder)

    sys.path.extend(paths)
    return paths
