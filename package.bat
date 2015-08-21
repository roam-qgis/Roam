@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to package Roam and all needed files using py2exe.  Result files will
REM be in the dist folder.

REM Change %OSGEO4W_ROOT% in setenv.bat to change in the location of QGIS.

REM ---------------------------------------------------------------------------------------

pushd %~dp0

call scripts/setenv.bat qgis

>package.log (
	make package
)
popd

ECHO Package in dist\
ECHO Check package.log for build log

if defined INSTALLER GOTO end
if defined DOUBLECLICKED pause

:end
