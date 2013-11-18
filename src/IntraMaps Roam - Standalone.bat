@ECHO OFF
: TODO Clean me up

SET OSGEO4W_ROOT=C:\Program Files\QGIS Dufour
SET QGIS=%OSGEO4W_ROOT%\apps\qgis

IF NOT EXIST %QGIS% (
    SET OSGEO4W_ROOT=C:\OSGeo4W
    SET QGIS=%OSGEO4W_ROOT%\apps\qgis
)

set QGIS_PREFIX_PATH=%QGIS%

: GDAL Setup
SET GDAL_DATA=%OSGEO4W_ROOT%\share\gdal
SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\bin\gdalplugins

: Python Setup
set PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%~dp0;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
set PYTHONPATH=%~dp0;%QGIS%\python;%~dp0qmap\editorwidgets\uifiles\;%PYTHONPATH%

: QT Setup
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\Qt4\plugins

:: set QGIS_DEBUG=0
:: set QGIS_LOG_FILE=qgis.log
:: set QGIS_DEBUG_FILE=qgis-debug.log

python qmap "%~dp0\projects"
