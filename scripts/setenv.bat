@ECHO OFF
REM ---------------------------------------------------------------------------------------
REM Setup environment for running/building Roam against OSGeo4W QGIS LTR
REM ---------------------------------------------------------------------------------------

for %%x in (%cmdcmdline%) do if /i "%%~x"=="/c" set DOUBLECLICKED=1

REM Resolve repo root from this script location
set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%..") do set BASE=%%~fI\

REM OSGeo4W root
IF NOT DEFINED OSGEO4W_ROOT SET OSGEO4W_ROOT=C:\OSGeo4W

REM QGIS package name
IF EXIST "%OSGEO4W_ROOT%\bin\qgis-ltr.bat" (
    SET QGISNAME=qgis-ltr
) ELSE (
    SET QGISNAME=qgis
)

REM Optional Git path
SET GIT=
IF EXIST "%PROGRAMFILES%\Git" (
    SET "GIT=%PROGRAMFILES%\Git"
) ELSE (
    IF EXIST "%PROGRAMFILES(X86)%\Git" (
        SET "GIT=%PROGRAMFILES(X86)%\Git"
    )
)

SET QGIS=%OSGEO4W_ROOT%\apps\%QGISNAME%
SET QGIS_PREFIX_PATH=%QGIS%

SET GDAL_DATA=%OSGEO4W_ROOT%\share\gdal
SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\bin\gdalplugins
SET PROJ_LIB=%OSGEO4W_ROOT%\share\proj

REM Python home used by OSGeo4W install
IF EXIST "%OSGEO4W_ROOT%\apps\Python312" (
    SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python312
)

REM IMPORTANT:
REM Newer OSGeo4W installs do not ship py3_env.bat / qt5_env.bat,
REM so we set the required paths directly.
SET PATH=%OSGEO4W_ROOT%\apps\Qt5\bin;%OSGEO4W_ROOT%\bin;%QGIS%\bin;%BASE%src;%GIT%\bin;%WINDIR%\system32;%WINDIR%;%WINDIR%\system32\WBem
SET QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\Qt5\plugins
SET PYTHONPATH=%BASE%src;%QGIS%\python;%BASE%ext_libs

ECHO Setup environment for
ECHO BASE: %BASE%
ECHO ROOT: %OSGEO4W_ROOT%
ECHO QGIS: %QGISNAME%
ECHO OSGeo path is: %OSGEO4W_ROOT%
ECHO Getting QGIS libs from: %QGIS%
ECHO Python loaded from: %PYTHONHOME%
ECHO PATH is: %PATH%
ECHO QT plugins from: %QT_PLUGIN_PATH%
ECHO Python libs from: %PYTHONPATH%
