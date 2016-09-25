@ECHO OFF

SET INSTALLER=1
pushd %~dp0
ECHO Creating release packages.
SET QGISNAME=qgis
CALL package.bat

REM Don't let the make_installer script call package again
SET DONTPACKAGE=1
CALL make_installer.bat
cd ..\dist
rm ..\release -rf
python -m zipfile -c "..\release\IntraMaps Roam.zip" .
