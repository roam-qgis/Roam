@ECHO OFF

cd /D %~dp0\admin

call setenv.bat
call python manager.py
pause