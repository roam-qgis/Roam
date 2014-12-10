@ECHO OFF
pushd %~dp0

call scripts/setenv.bat

make test

if defined DOUBLECLICKED pause
