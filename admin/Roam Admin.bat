@ECHO OFF

call %~dp0setenv.bat
call python %~dp0manager.py
pause