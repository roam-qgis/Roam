@ECHO OFF

cd /D %~dp0\qmap-admin

call setenv.bat
call python manager.py
pause