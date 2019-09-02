"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""
import os
import sys

srcpath = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(srcpath)

frozen = getattr(sys, "frozen", False)
RUNNING_FROM_FILE = not frozen

import gdal

if frozen:
    os.environ['PATH'] = "{0};{1}".format(os.path.join(srcpath, 'libs'), srcpath)
    os.environ["GDAL_DRIVER_PATH"] = os.path.join(srcpath, 'libs')
    os.environ["GDAL_DATA"] = os.path.join(srcpath, 'libs', 'gdal')

os.environ['OGR_SQLITE_PRAGMA'] = "journal_mode=delete"
gdal.SetConfigOption('OGR_SQLITE_PRAGMA', os.environ['OGR_SQLITE_PRAGMA'])
gdal.SetConfigOption("GDAL_DRIVER_PATH", os.environ['GDAL_DRIVER_PATH'])
gdal.SetConfigOption("GDAL_DATA", os.environ['GDAL_DATA'])

from roam import utils, environ

config = {"loglevel": "DEBUG"}

utils.setup_logging(srcpath, config)

with environ.setup(srcpath) as roamapp:
    import roam.config
    import roam
    import roam.mainwindow

    roam.utils.info("Runtime logging at: {}".format(roamapp.profileroot))
    roam.utils.setup_logging(roamapp.profileroot, roam.config.settings)

    roam.utils.debug("Environment:")
    roam.utils.debug(os.environ["GDAL_DRIVER_PATH"])
    roam.utils.debug(os.environ["GDAL_DATA"])
    roam.utils.debug(os.environ["PATH"])

    from qgis.core import QgsProviderRegistry

    ecwsupport = 'ecw' in QgsProviderRegistry.instance().fileRasterFilters()
    roam.utils.info("ECW Support: {0}".format(ecwsupport))

    window = roam.mainwindow.MainWindow(roamapp)

    roamapp.setActiveWindow(window)
    roamapp.set_error_handler(window.raiseerror, roam.utils)

    projectpaths = roam.environ.projectpaths(roamapp.projectsroot,
                                             roam.config.settings)
    projects = roam.project.getProjects(projectpaths)
    window.load_projects(projects)
    window.actionProject.toggle()
    window.show_project_list()
    pluginpath = os.path.join(os.path.dirname(roamapp.settingspath), "plugins")
    apppluginpath = os.path.join(roamapp.apppath, "plugins")

    import roam.api.plugins

    roam.api.plugins.load_plugins_from([pluginpath, apppluginpath])
    window.show()
