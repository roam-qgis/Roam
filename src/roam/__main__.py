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

if frozen:
    os.environ['PATH'] += ";{}".format(os.path.join(srcpath, 'libs'))
    os.environ['PATH'] += ";{}".format(srcpath)
    os.environ["GDAL_DRIVER_PATH"] = os.path.join(srcpath, 'libs')
    os.environ["GDAL_DATA"] = os.path.join(srcpath, 'libs', 'gdal')
    os.environ['OGR_SQLITE_PRAGMA'] = "journal_mode=WAL"


import roam.environ

with roam.environ.setup(srcpath) as roamapp:
    import roam.config
    import roam
    import roam.mainwindow
    import roam.utils


    window = roam.mainwindow.MainWindow(roamapp)

    roamapp.setActiveWindow(window)
    roamapp.set_error_handler(window.raiseerror, roam.utils)

    projectpaths = roam.environ.projectpaths(roamapp.projectsroot,
                                             roam.config.settings)
    projects = roam.project.getProjects(projectpaths)
    window.loadprojects(projects)
    window.actionProject.toggle()
    window.viewprojects()
    pluginpath = os.path.join(os.path.dirname(roamapp.settingspath), "plugins")
    apppluginpath = os.path.join(roamapp.apppath, "plugins")

    import roam.api.plugins
    roam.api.plugins.load_plugins_from([pluginpath, apppluginpath])
    window.show()
