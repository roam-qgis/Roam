@ECHO OFF

SET INSTALLER=1
pushd %~dp0
ECHO Creating installer package.
CALL ..\package.bat
..\installer\makesfx.bat "IntraMaps Roam Installer" ..\dist\
popd

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1
if defined DOUBLECLICKED pause
