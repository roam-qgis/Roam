@ECHO OFF

call src\setenv.bat

call python qmap-admin\manager.py
pause