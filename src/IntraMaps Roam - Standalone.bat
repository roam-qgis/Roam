@ECHO OFF
set OSGEO4W_ROOT=C:\OSGeo4W
SET GDAL_DATA=%OSGEO4W_ROOT%\share\gdal

SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\bin\gdalplugins

set PATH=%OSGEO4W_ROOT%\bin;%OSGEO4W_ROOT%\apps\qgis-dev\bin;%~dp0;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
set PYTHONPATH=%~dp0;%OSGEO4W_ROOT%\apps\qgis-dev\python;%~dp0qmap\qtcontrols;..\%~dp0;%PYTHONPATH%
SET PYQTDESIGNERPATH=%~dp0qmap\qtcontrols\plugins
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\Qt4\plugins

set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis-dev\
:: set QGIS_DEBUG=0
:: set QGIS_LOG_FILE=qgis.log
:: set QGIS_DEBUG_FILE=qgis-debug.log

python qmap %~dp0\..\projects