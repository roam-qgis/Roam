import os
import sys
import time
import argparse
import contextlib
import functools


class RoamApp(object):
    def __init__(self, sysargv, apppath, prefixpath, settingspath, libspath, i18npath, projectsroot):
        self.sysargv = sysargv
        self.apppath = apppath
        self.prefixpath = prefixpath
        self.settingspath = settingspath
        self.libspath = libspath
        self.i18npath = i18npath
        self.app = None
        self.translationFile = None
        self.projectsroot = projectsroot
        self._oldhook = sys.excepthook

    def init(self, logo, title):
        from qgis.core import QgsApplication
        from PyQt4.QtGui import QApplication, QFont, QIcon
        from PyQt4.QtCore import QLocale, QTranslator
        try:
            import PyQt4.QtSql
        except ImportError:
            pass

        self.app = QgsApplication(self.sysargv, True)
        import roam.roam_style
        self.app.setStyleSheet(roam.roam_style.appstyle)
        QgsApplication.setPrefixPath(self.prefixpath, True)
        QgsApplication.initQgis()

        locale = QLocale.system().name()
        self.translationFile = os.path.join(self.i18npath, '{0}.qm'.format(locale))
        translator = QTranslator()
        translator.load(self.translationFile, "i18n")
        self.app.installTranslator(translator)

        QApplication.setStyle("Plastique")
        QApplication.setFont(QFont('Segoe UI'))
        QApplication.setWindowIcon(QIcon(logo))
        QApplication.setApplicationName(title)

        import roam.editorwidgets.core
        roam.editorwidgets.core.registerallwidgets()
        import roam.qgisfunctions
        return self

    def set_error_handler(self, errorhandler, logger):
        sys.excepthook = functools.partial(self.excepthook, errorhandler)
        self.logger = logger

    def excepthook(self, errorhandler, exctype, value, traceback):
        self.logger.error("Uncaught exception", exc_info=(exctype, value, traceback))
        errorhandler(exctype, value, traceback)

    def exec_(self):
        self.app.exec_()

    def exit(self):
        sys.excepthook = self._oldhook
        from qgis.core import QgsApplication
        QgsApplication.exitQgis()
        QgsApplication.quit()

    def setActiveWindow(self, widget):
        self.app.setActiveWindow(widget)

    def dump_configinfo(self):
        from qgis.core import QgsApplication, QgsProviderRegistry
        from PyQt4.QtGui import QImageReader, QImageWriter
        import roam
        from qgis.core import QGis

        config = []
        config.append("====Providers===")
        config.append(QgsProviderRegistry.instance().pluginList())
        config.append("====Library paths===")
        config.append('\n'.join(QgsApplication.libraryPaths()))
        config.append("====Translation File===")
        config.append(self.translationFile)
        config.append("Roam Version: {}".format(roam.__version__))
        config.append("QGIS Version: {}".format(str(QGis.QGIS_VERSION)))
        return '\n'.join(config)

def _setup(apppath=None, logo='', title='', **kwargs):
    frozen = getattr(sys, "frozen", False)
    RUNNING_FROM_FILE = not frozen
    if not apppath:
        apppath = os.path.dirname(os.path.realpath(sys.argv[0]))

    if RUNNING_FROM_FILE:
        print "Running from file"
        print os.getcwd()
        print apppath
        i18npath = os.path.join(apppath, "i18n")
        if os.name == 'posix':
            prefixpath = os.environ.get('QGIS_PREFIX_PATH', '/usr/')
        else:
            prefixpath = os.environ['QGIS_PREFIX_PATH']
        libspath = prefixpath
        projectroot = os.path.join(apppath, "..")
    else:
        # Set the PATH and GDAL_DRIVER_PATH for gdal to find the plugins.
        # Not sure why we have to set these here but GDAL doesn't like it if we
        # don't
        prefixpath = os.path.join(apppath, "libs", "qgis")
        libspath = os.path.join(apppath, "libs", "roam")
        i18npath = os.path.join(libspath, "i18n")

        os.environ['PATH'] += ";{}".format(os.path.join(apppath, 'libs'))
        os.environ['PATH'] += ";{}".format(apppath)
        os.environ["GDAL_DRIVER_PATH"] = os.path.join(apppath, 'libs')
        os.environ["GDAL_DATA"] = os.path.join(apppath, 'libs', 'gdal')
        projectroot = apppath

    projectroot = os.path.join(projectroot, "projects")

    try:
        settingspath = kwargs['config']
    except KeyError:
        settingspath = os.path.join(apppath, "roam.config")
        if not os.path.exists(settingspath):
            settingspath = os.path.join(apppath, "settings.config")

    parser = argparse.ArgumentParser(description="IntraMaps Roam")
    parser.add_argument('--config', metavar='c', type=str, default=settingspath, help='Path to Roam.config')
    parser.add_argument('projectsroot', nargs='?', default=projectroot, help="Root location of projects. Will override"
                                                                             "default projects folder path")
    args, unknown = parser.parse_known_args()

    if not os.path.exists(args.projectsroot):
        os.makedirs(args.projectsroot)

    app = RoamApp(sys.argv, apppath, prefixpath, args.config, libspath, i18npath, args.projectsroot).init(logo, title)
    import roam.config
    roam.config.load(app.settingspath)
    return app


@contextlib.contextmanager
def setup(apppath=None, logo='', title=''):
    """
    Setup the environment for Roam.

    Returns the QGIS prefix path and settings path.
    """
    import roam.utils
    import roam.config
    roam.utils.info("Loading Roam")
    start = time.time()
    app = _setup(apppath, logo, title)
    roam.utils.info("Roam Loaded in {}".format(str(time.time() - start)))
    roam.utils.info(app.dump_configinfo())
    yield app
    app.exec_()
    roam.config.save()
    app.exit()


def projectpaths(baseprojectpath, settings={}):
    # Add the default paths
    paths = []
    paths.append(baseprojectpath)
    paths.extend(settings.get('projectpaths', []))
    for path in paths:
        rootfolder = os.path.abspath(os.path.join(path, '..'))
        sys.path.append(rootfolder)

    sys.path.extend(paths)
    import roam.utils
    roam.utils.log("Project locations:{}".format(paths))
    return paths
