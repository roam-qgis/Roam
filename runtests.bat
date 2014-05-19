@ECHO OFF
pushd %~dp0

call scripts/setenv.bat

python -m pytest tests

if defined DOUBLECLICKED pause
