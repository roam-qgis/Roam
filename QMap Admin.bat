@ECHO OFF

call src\setenv.bat

cd %~dp0

call python qmap-admin\manager.py
pause