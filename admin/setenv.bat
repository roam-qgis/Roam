@ECHO OFF

SET OSGEO4W_ROOT=C:\OSGeo4W

PATH="%OSGEO4W_ROOT%\bin";%PATH%
for %%f in ("%OSGEO4W_ROOT%\etc\ini\*.bat") do call "%%f"

SET QGIS_PLUGINPATH=%~dp0..\qgis_plugin\
set QGISHOME="%OSGEO4W_ROOT%\apps\qgis-dev\"
SET PYTHONPATH=%~dp0qtcontrols;%~dp0;%PYTHONPATH%
SET PYQTDESIGNERPATH=%~dp0qtcontrols\plugins