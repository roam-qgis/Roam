@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to setup the environment for building Roam with QGIS 3.x.
REM This script sets the base folder that is used though out the build process
REM and sets the location to Python.

REM ---------------------------------------------------------------------------------------

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1

SET OSGEO4W_ROOT=
FOR /D %%p in ("%PROGRAMFILES%\QGIS 3.*","%PROGRAMFILES(X86)%\QGIS 3.*") DO (
    SET OSGEO4W_ROOT="%%~fsp"
)

REM Change OSGeo4W_ROOT here to point to your install of QGIS if it is not in the standard directories.
IF NOT DEFINED OSGEO4W_ROOT SET OSGEO4W_ROOT=C:\OSGeo4W
SET OSGEO4W_ROOT=%OSGEO4W_ROOT:"=%

IF EXIST "%OSGEO4W_ROOT%\bin\qgis-ltr.bat" (
    SET QGISNAME=qgis-ltr
) ELSE (
    SET QGISNAME=qgis
)

IF EXIST "%PROGRAMFILES%\Git\bin" (
    SET GIT="%PROGRAMFILES%\Git"
) ELSE (
    SET GIT="%PROGRAMFILES(X86)%\Git"
)
SET GIT=%GIT:"=%

ECHO Setup environment for
ECHO ROOT: %OSGEO4W_ROOT%
ECHO QGIS: %QGISNAME%
SET QGIS=%OSGEO4W_ROOT%\apps\%QGISNAME%
set QGIS_PREFIX_PATH=%QGIS%

SET GDAL_DATA=%OSGEO4W_ROOT%\share\gdal
SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\bin\gdalplugins
SET PROJ_LIB=%OSGEO4W_ROOT%\share\proj

set PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%BASE%\src\;%GIT%\bin;;%WINDIR%\system32;%WINDIR%;%WINDIR%\system32\WBem

: Python Setup
CALL %OSGEO4W_ROOT%\bin\py3_env.bat

ECHO OSGeo path is: %OSGEO4W_ROOT%
ECHO Getting QGIS libs from: %QGIS%
ECHO Python loaded from: %PYTHONHOME%
ECHO PATH is: %PATH%
