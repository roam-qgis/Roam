@ECHO OFF
set OSGEO4W_ROOT=C:\OSGeo4W
SET GDAL_DATA=%OSGEO4W_ROOT%\share\gdal

SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\bin\gdalplugins

set PATH=%OSGEO4W_ROOT%\bin;%OSGEO4W_ROOT%\apps\qgis-dev\bin;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis-dev\python
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis-dev\
set QGIS_DEBUG=0
set QGIS_LOG_FILE=qgis.log
set QGIS_DEBUG_FILE=qgis-debug.log

python qmap ..\projects
pause
