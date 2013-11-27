@ECHO OFF

call %~dp0setenv.bat

python setup.py py2exe

pause
