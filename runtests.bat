@ECHO OFF
pushd %~dp0

call scripts/setenv.bat

py.test src/roam.tests

if defined DOUBLECLICKED pause
