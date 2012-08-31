@ECHO OFF
REM Run the batch file to remove all the normal QGIS interface.
REGEDIT /s StripInterface.reg
C:\OSGeo4w\bin\qgis-dev.bat --configpath "./app" --optionspath "./app"