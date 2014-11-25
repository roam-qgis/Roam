@ECHO OFF
pushd %~dp0

call scripts/setenv.bat

py.test tests %*

if defined DOUBLECLICKED pause
