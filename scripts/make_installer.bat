@ECHO OFF

SET INSTALLER=1
pushd %~dp0
ECHO Creating installer package.
CALL ..\package.bat
MKDIR ..\release
installer\makesfx.bat "..\release\IntraMaps Roam Installer" ..\dist\

