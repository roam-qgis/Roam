@ECHO OFF
set OSGEO4W_ROOT=C:\OSGeo4W
set PATH=%OSGEO4W_ROOT%\bin;%OSGEO4W_ROOT%\apps\qgis-dev\bin;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis-dev\python;%~dp0qtcontrols;%PYTHONPATH%
SET PYQTDESIGNERPATH=%~dp0qtcontrols\plugins
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis-dev\
START C:\OSGeo4W\bin\designer.exe
