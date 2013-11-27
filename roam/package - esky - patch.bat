@ECHO OFF

SET OSGEO4W_ROOT=C:\OSGeo4W
SET QGIS=%OSGEO4W_ROOT%\apps\qgis-dev

: Look for QGIS in Program files if it's not in the normal place
IF NOT EXIST %QGIS% (
    SET OSGEO4W_ROOT=C:\Program Files\QGIS Dufour
    SET QGIS=%OSGEO4W_ROOT%\apps\qgis
)

set QGIS_PREFIX_PATH=%QGIS%

: Python Setup
set PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%~dp0\src\;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
set PYTHONPATH=%~dp0\src;%QGIS%\python;%~dp0qmap\editorwidgets\uifiles\;%PYTHONPATH%

: QT Setup
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\Qt4\plugins

python setup.py bdist_esky_patch

pause
