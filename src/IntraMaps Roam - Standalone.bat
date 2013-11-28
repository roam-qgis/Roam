@ECHO OFF
setlocal enableextensions enabledelayedexpansion

pushd %~dp0
CALL setenv.bat
python roam "%~dp0\projects"
popd
pause

