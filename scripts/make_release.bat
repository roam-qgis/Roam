@ECHO OFF

SET INSTALLER=1
pushd %~dp0
ECHO Creating release packages.
CALL setenv.bat
CALL ..\package.bat
CALL make_installer.bat
cd ..\dist
zip "..\release\IntraMaps Roam.zip" . -r

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1
if defined DOUBLECLICKED pause
