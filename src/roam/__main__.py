"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""

import os
import sys

import time
import functools

srcpath = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(srcpath)

import roam.environ
import roam.config

roamapp = roam.environ.setup(sys.argv)
roam.config.load(roamapp.settingspath)

import roam
import roam.mainwindow
import roam.utils
import roam.api.featureform


# Fake this module to maintain API.
sys.modules['roam.featureform'] = roam.api.featureform

roam.utils.info(list(roamapp.dump_configinfo()))

start = time.time()
roam.utils.info("Loading Roam")

window = roam.mainwindow.MainWindow()
roamapp.setActiveWindow(window)

def excepthook(errorhandler, exctype, value, traceback):
    errorhandler(exctype, value, traceback)
    roam.utils.error("Uncaught exception", exc_info=(exctype, value, traceback))

sys.excepthook = functools.partial(excepthook, window.raiseerror)

projectpaths = roam.environ.projectpaths(sys.argv, roamapp, roam.config.settings)
roam.utils.log("Loading projects from")
roam.utils.log(projectpaths)
projects = roam.project.getProjects(projectpaths)
window.loadprojects(projects)
window.actionProject.toggle()
window.viewprojects()

from roam.api import plugins

pluginspath = os.path.join(roamapp.apppath, "plugins")
print pluginspath
plugins.load_plugins_from([pluginspath])

window.loadpages(plugins.registeredpages)
window.show()

roam.utils.info("Roam Loaded in {}".format(str(time.time() - start)))

roamapp.exec_()
roamapp.exit()
