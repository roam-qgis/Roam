@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to package Roam and all needed files using py2exe.  Result files will
REM be in the dist folder.

REM ---------------------------------------------------------------------------------------

pushd %~dp0

CALL setenv.bat

>..\build\package.log (
    ..\build.bat package
)
popd

ECHO Package in dist\
ECHO Check package.log for build log

if defined INSTALLER GOTO end
if defined DOUBLECLICKED pause

:end
