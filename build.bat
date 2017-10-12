@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to build the resource and UI files. You only really need to run this if you are
REM running from source.  Package.bat will build all the resources before it creates the package

REM Change %OSGEO4W_ROOT% in setenv.bat to change in the location of QGIS.

REM ---------------------------------------------------------------------------------------

pushd %~dp0
call scripts\setenv.bat
IF "%1"=="" goto build
IF "%1"=="package" goto package

IF "%1"=="watch" (
    python scripts\watchui.py
    exit
)

:build
ECHO Building..
python setup.py clean
python setup.py build
GOTO END

:package
ECHO Making package..
python setup.py clean
python setup.py build
python setup.py py2exe
GOTO END

:END
popd
if defined DOUBLECLICKED pause
