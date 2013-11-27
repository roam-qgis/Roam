@ECHO OFF

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1

SET OSGEO4W_ROOT=C:\OSGeo4W
SET QGIS=%OSGEO4W_ROOT%\apps\qgis-dev
set QGIS_PREFIX_PATH=%QGIS%

: Python Setup
set PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%~dp0\src\;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
set PYTHONPATH=%~dp0\src;%QGIS%\python;%PYTHONPATH%
