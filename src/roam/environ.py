import os
import sys
import argparse

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

    def init(self):
        from qgis.core import QgsApplication
        from PyQt4.QtGui import QApplication, QFont
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
    apppath = os.path.dirname(os.path.realpath(argv[0]))
    if RUNNING_FROM_FILE:
        print "Running from file"
        i18npath = os.path.join(apppath, "i18n")
        if os.name == 'posix':
            prefixpath = os.environ.get('QGIS_PREFIX_PATH', '/usr/')
        else:
            prefixpath = os.environ['QGIS_PREFIX_PATH']
        libspath = prefixpath
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


    settingspath = os.path.join(apppath, "roam.config")
    if not os.path.exists(settingspath):
        settingspath = os.path.join(apppath, "settings.config")

    projectpath = os.path.join(apppath, "projects")

    parser = argparse.ArgumentParser(description="IntraMaps Roam")
    parser.add_argument('--config', metavar='c', type=str, default=settingspath, help='Path to Roam.config')
    parser.add_argument('--projectsroot', metavar='p', type=str, default=projectpath, help='Root location of projects. Will soverride'
                                                                                            'default projects folder location')

    args = parser.parse_args()

    return RoamApp(argv, apppath, prefixpath, args.config, libspath, i18npath, args.projectsroot).init()


def projectpaths(baseprojectpath, settings={}):
    # Add the default paths
    paths = []
    paths.append(baseprojectpath)
    paths.extend(settings.get('projectpaths', []))
    for path in paths:
        rootfolder = os.path.abspath(os.path.join(path, '..'))
        sys.path.append(rootfolder)

    sys.path.extend(paths)
    return paths
