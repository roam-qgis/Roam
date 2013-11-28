@ECHO OFF

pushd %~dp0
call setenv.bat
python setup.py clean && python setup.py build
popd
if defined DOUBLECLICKED pause
