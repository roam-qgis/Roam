@ECHO OFF
setlocal enableextensions enabledelayedexpansion

CALL "%~dp0setenv.bat"

python qmap "%~dp0\..\projects"

pause

