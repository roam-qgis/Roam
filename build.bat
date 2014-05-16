@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to build the resource and UI files. You only really need to run this if you are
REM running from source.  Package.bat will build all the resources before it creates the package

REM Change %OSGEO4W_ROOT% in setenv.bat to change in the location of QGIS.

REM ---------------------------------------------------------------------------------------

pushd %~dp0
call scripts\setenv.bat
IF "%1"=="" goto build

IF "%1"=="watch" (
    python scripts\watchui.py
    exit
)

:build
python setup.py clean && python setup.py build
popd

if defined DOUBLECLICKED pause
