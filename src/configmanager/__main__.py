import os
import sys
import functools

srcpath = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(srcpath)

frozen = getattr(sys, "frozen", False)
RUNNING_FROM_FILE = not frozen

if frozen:
    os.environ['PATH'] += ";{}".format(os.path.join(srcpath, 'libs'))
    os.environ['PATH'] += ";{}".format(srcpath)
    os.environ["GDAL_DRIVER_PATH"] = os.path.join(srcpath, 'libs')
    os.environ["GDAL_DATA"] = os.path.join(srcpath, 'libs', 'gdal')

import roam.environ

with roam.environ.setup(logo=':/branding/config', title="IntraMaps Roam Config Manager") as roamapp:
    import roam
    import roam.config
    import configmanager.logger
    from configmanager.ui.configmanagerdialog import ConfigManagerDialog

    dialog = ConfigManagerDialog()
    roamapp.set_error_handler(dialog.raiseerror, configmanager.logger)

    projectpaths = roam.environ.projectpaths(roamapp.projectsroot, roam.config.settings)
    dialog.addprojectfolders(projectpaths)
    dialog.showMaximized()

