@ECHO OFF

call %~dp0setenv.bat

python %~dp0build.py clean
python %~dp0build.py
