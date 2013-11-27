@ECHO OFF

call %~dp0setenv.bat

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1

python setup.py clean --all
python setup.py py2exe 2>&1 | type py2exe.log

if defined DOUBLECLICKED pause
