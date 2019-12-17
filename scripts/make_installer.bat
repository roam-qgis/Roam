@ECHO OFF

SET INSTALLER=1
pushd %~dp0
ECHO Creating installer package.
SET QGISNAME=qgis
IF NOT DEFINED DONTPACKAGE (CALL package.bat)
MKDIR ..\release
CALL installer\makesfx.bat "..\release\Roam Installer" ..\dist\
CALL installer\makesfx.bat "..\release\Roam Installer - Silent" ..\dist\ -s
