SET OSGEO4W_ROOT=C:\OSGeo4W\
call "%OSGEO4W_ROOT%"\bin\o4w_env.bat
call "%OSGEO4W_ROOT%"\apps\grass\grass-6.4.3RC2\etc\env.bat
@echo off
path %PATH%;%OSGEO4W_ROOT%\apps\qgis-dev\bin;%OSGEO4W_ROOT%\apps\grass\grass-6.4.3RC2\lib
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/qgis-dev
SET PYTHONPATH=.\qtcontrols
SET PYQTDESIGNERPATH=.\qtcontrols
start "Quantum GIS" /B "%OSGEO4W_ROOT%"\bin\qgis-dev.exe %*