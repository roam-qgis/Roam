@ECHO OFF
CD %~dp0
call qmap-admin\setenv.bat
python qmap-admin\build.py -o "Melton Install"
pause