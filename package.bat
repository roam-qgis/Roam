@ECHO OFF

call %~dp0setenv.bat

call build.bat
python setup.py py2exe

if defined DOUBLECLICKED pause
