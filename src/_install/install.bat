@ECHO OFF
setlocal enableextensions enabledelayedexpansion

CALL ..\setenv.bat

TITLE IntraMaps Roam Installer
pythonw -m compileall "%~dp0\..\qmap"
python "%~dp0postinstall.py" --save
pause
