@ECHO OFF

cd /D %~dp0

call qmap-admin\setenv.bat
call python qmap-admin\manager.py
pause