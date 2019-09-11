import os
import sys
import functools

srcpath = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(srcpath)

frozen = getattr(sys, "frozen", False)
RUNNING_FROM_FILE = not frozen

if frozen:
    os.environ['PATH'] = "{0};{1}".format(os.path.join(srcpath, 'lib'), srcpath)
    os.environ["GDAL_DRIVER_PATH"] = os.path.join(srcpath, 'lib')
    os.environ["GDAL_DATA"] = os.path.join(srcpath, 'lib', 'gdal')

os.environ['OGR_SQLITE_PRAGMA'] = "journal_mode=delete"

import gdal
gdal.SetConfigOption("GDAL_DRIVER_PATH", os.environ['GDAL_DRIVER_PATH'])
gdal.SetConfigOption("GDAL_DATA", os.environ['GDAL_DATA'])
gdal.SetConfigOption('OGR_SQLITE_PRAGMA', os.environ['OGR_SQLITE_PRAGMA'])

from roam import utils, environ
config = {"loglevel": "DEBUG"}

utils.setup_logging(srcpath, config)

import roam.environ

with roam.environ.setup(logo=':/branding/config', title="IntraMaps Roam Config Manager") as roamapp:
    import roam.config
    import configmanager.logger
    import roam.errors

    from configmanager.config import Config
    from configmanager.ui.configmanagerdialog import ConfigManagerDialog

    roam.errors.init_error_handler()

    managerconfig = Config.from_file(os.path.join(roamapp.profileroot,"configmanager.config"))
    roamapp.config = managerconfig

    roam.utils.setup_logging(roamapp.profileroot, roam.config.settings)

    roamapp.app.setStyleSheet(roam.roam_style.appstyle())
    dialog = ConfigManagerDialog(roamapp)
    roamapp.set_error_handler(dialog.raiseerror, configmanager.logger)

    projectpaths = roam.environ.projectpaths(roamapp.projectsroot, roam.config.settings)
    dialog.addprojectfolders(projectpaths)
    dialog.showMaximized()

