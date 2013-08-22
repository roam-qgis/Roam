@ECHO OFF

:: SET OSGEO4W_ROOT=%~dp0qgis
SET OSGEO4W_ROOT=C:\OSGeo4W
PATH="%OSGEO4W_ROOT%\bin";%PATH%
for %%f in ("%OSGEO4W_ROOT%\etc\ini\*.bat") do call "%%f"

SET QGIS_PLUGINPATH=%~dp0
SET PYTHONPATH=%~dp0qmap\qtcontrols;%~dp0;%PYTHONPATH%
SET PYQTDESIGNERPATH=%~dp0qmap\qtcontrols\plugins