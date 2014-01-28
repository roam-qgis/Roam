import os
import sys


def setup(argv):
    """
    Setup the environment for Roam.

    Returns the QGIS prefix path and settings path.
    """
    RUNNING_FROM_FILE = '__file__' in globals()
    apppath = os.path.dirname(os.path.realpath(argv[0]))
    prefixpath = os.path.join(apppath, "libs", "qgis")
    settingspath = os.path.join(apppath, "settings.config")

    # Set the PATH and GDAL_DRIVER_PATH for gdal to find the plugins.
    # Not sure why we have to set these here but GDAL doesn't like it if we
    # don't
    os.environ['PATH'] += ";{}".format(os.path.join(apppath, 'libs'))
    os.environ["GDAL_DRIVER_PATH"] = os.path.join(apppath, 'libs')

    if RUNNING_FROM_FILE:
        print "Running from file"
        # Setup the paths for OSGeo4w if we are running from a file
        # this means that we are not running from a frozen app.
        os.environ['PATH'] += r";C:\OSGeo4W\bin;C:\OSGeo4W\apps\qgis\bin"
        sys.path.append(r"C:\OSGeo4W\apps\qgis\python")
        os.environ["GDAL_DATA"] = r"C:\OSGeo4W\share\gdal"
        os.environ["GDAL_DRIVER_PATH"] = r"C:\OSGeo4W\bin\gdalplugins"
        os.environ["QT_PLUGIN_PATH"] = r"C:\OSGeo4W\apps\Qt4\plugins"
        prefixpath = r"C:\OSGeo4W\apps\qgis"
        settingspath = os.path.join(apppath, "..", "settings.config")

    return prefixpath, settingspath
