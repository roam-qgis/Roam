@ECHO OFF

SET INSTALLER=1
pushd %~dp0
ECHO Creating release packages.
SET QGISNAME=qgis
CALL package.bat
CALL make_installer.bat
cd ..\dist
rm ..\release -rf
python -m zipfile -c "..\release\IntraMaps Roam.zip" .
