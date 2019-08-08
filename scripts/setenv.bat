@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to setup the environment for building Roam with QGIS 3.x.
REM This script sets the base folder that is used though out the build process
REM and sets the location to Python.

REM ---------------------------------------------------------------------------------------

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1

FOR /D %%p in ("C:\Program Files\QGIS 3.*","C:\Program Files (x86)\QGIS 3.*") DO (
    SET OSGEO4W_ROOT=%%p
)

REM Change OSGeo4W_ROOT here to point to your install of QGIS if it is not in the standard directories.
IF NOT DEFINED OSGEO4W_ROOT SET OSGEO4W_ROOT=C:\OSGeo4W

IF EXIST %OSGEO4W_ROOT%\bin\qgis-ltr.bat (
    SET QGISNAME=qgis-ltr
) ELSE (
    SET QGISNAME=qgis
)

ECHO Setup environment for
ECHO ROOT: %OSGEO4W_ROOT%
ECHO QGIS: %QGISNAME%
SET QGIS=%OSGEO4W_ROOT%\apps\%QGISNAME%
set QGIS_PREFIX_PATH=%QGIS%

CALL "%OSGEO4W_ROOT%\bin\o4w_env.bat"

: Python Setup
SET BASE=%~dp0..\
set PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%BASE%\src\;C:\Program Files (x86)\Git\bin;%PATH%;
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
set PYTHONPATH=%BASE%\src;%QGIS%\python;%BASE%\libs

ECHO OSGeo path is: %OSGEO4W_ROOT%
ECHO Getting QGIS libs from: %QGIS%
ECHO Python loaded from: %PYTHONHOME%
ECHO PATH is: %PATH%
ECHO Python libs from: %PYTHONPATH%
