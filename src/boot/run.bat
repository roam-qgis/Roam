@ECHO OFF
REGEDIT /e qgis-customization.reg "HKEY_CURRENT_USER\Software\QuantumGIS\QGISCUSTOMIZATION"
REM Run the batch file to remove all the normal QGIS interface.
REGEDIT /s StripInterface.reg
C:\OSGeo4w\bin\qgis-dev.bat --configpath "./app" --optionspath "./app"