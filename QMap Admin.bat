@ECHO OFF

call qmap-admin\setenv.bat

cd %~dp0

call python qmap-admin\manager.py
pause