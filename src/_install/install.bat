@ECHO OFF

CALL ..\setenv.bat

TITLE IntraMaps Roam Installer
python "%~dp0postinstall.py" --save
pause
