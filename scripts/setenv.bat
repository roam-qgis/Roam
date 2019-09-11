@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to setup the environment for building Roam with QGIS 3.x.
REM This script sets the base folder that is used though out the build process
REM and sets the location to Python.

REM ---------------------------------------------------------------------------------------

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1

REM Change OSGeo4W_ROOT here to point to your install of QGIS if it is not in the standard directories.
IF NOT DEFINED OSGEO4W_ROOT SET OSGEO4W_ROOT="C:\PROGRA~1\QGIS3~1.4"
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
ECHO BASE: %BASE%
ECHO ROOT: %OSGEO4W_ROOT%
ECHO QGIS: %QGISNAME%
SET QGIS=%OSGEO4W_ROOT%\apps\%QGISNAME%
set QGIS_PREFIX_PATH=%QGIS%

SET GDAL_DATA=%OSGEO4W_ROOT%\share\gdal
SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\bin\gdalplugins
SET PROJ_LIB=%OSGEO4W_ROOT%\share\proj

SET PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%BASE%\src\;%GIT%\bin;;%WINDIR%\system32;%WINDIR%;%WINDIR%\system32\WBem;

: Python Setup
CALL %OSGEO4W_ROOT%\bin\py3_env.bat
CALL %OSGEO4W_ROOT%\bin\qt5_env.bat
SET PYTHONPATH=%BASE%\src;%QGIS%\python

ECHO OSGeo path is: %OSGEO4W_ROOT%
ECHO Getting QGIS libs from: %QGIS%
ECHO Python loaded from: %PYTHONHOME%
ECHO PATH is: %PATH%
ECHO Python libs from: %PYTHONPATH%
