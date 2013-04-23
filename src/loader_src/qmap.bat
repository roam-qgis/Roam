@ECHO OFF
set QGIS_PLUGINPATH=%~dp0
SET PYTHONPATH=qmap\qtcontrols
SET PYQTDESIGNERPATH=qmap\qtcontrols
"C:\OSGeo4W\bin\qgis-dev.bat" --configpath "qmap\app" --optionspath "qmap\app"