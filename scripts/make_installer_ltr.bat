@ECHO OFF

SET INSTALLER=1
pushd %~dp0
ECHO Creating installer package.
SET QGISNAME=qgis-ltr
CALL ..\package.bat
MKDIR ..\release
CALL installer\makesfx.bat "..\release\IntraMaps Roam Installer" ..\dist\
CALL installer\makesfx.bat "..\release\IntraMaps Roam Installer - Silent" ..\dist\ -s
