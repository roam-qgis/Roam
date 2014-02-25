@ECHO OFF
for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1

pushd %~dp0
ECHO Creating installer package.
installer\makesfx.bat "IntraMaps Roam Installer" dist\
popd

if defined DOUBLECLICKED pause
