import os
import sys
import functools

srcpath = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(srcpath)

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

