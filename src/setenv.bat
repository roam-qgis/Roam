@ECHO OFF

SET OSGEO4W_ROOT=F:\qgis_install\QGIS Weekly

:: Uncomment the following line if QGIS is installed in the
:: current folder.  

:: SET OSGEO4W_ROOT=%~dp0qgis

PATH=%OSGEO4W_ROOT%\bin;%OSGEO4W_ROOT%\apps\qgis-dev\bin;%PATH%
for %%f in ("%OSGEO4W_ROOT%\etc\ini\*.bat") do call "%%f"

SET QGIS_PLUGINPATH=%~dp0
SET PYTHONPATH=%~dp0qmap\qtcontrols;%~dp0;%OSGEO4W_ROOT%\apps\qgis-dev\python;%PYTHONPATH%
SET PYQTDESIGNERPATH=%~dp0qmap\qtcontrols\plugins