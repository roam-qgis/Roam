@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to build the resource and UI files. You only really need to run this if you are
REM running from source.  Package.bat will build all the resources before it creates the package

REM Change %OSGEO4W_ROOT% in setenv.bat to change in the location of QGIS.

REM ---------------------------------------------------------------------------------------

pushd %~dp0

call scripts\setenv.bat %1
IF "%2"=="" goto build
GOTO %2

:watch
python scripts\watchui.py
exit

:build
ECHO Building..
python setup.py clean
python setup.py build
GOTO END

:exe
ECHO Making package..
python setup.py clean
python setup.py build
python setup.py py2exe
GOTO END

:release
ECHO Building release
python setup.py clean
python setup.py build
python setup.py py2exe
IF NOT EXIST release MKDIR release
del release\*.* /Q /F
pushd dist
ECHO Making zip file..
SET NAME=%3
python -m zipfile -c "..\release\IntraMaps Roam%NAME%.zip" .
GOTO END

:installer
ECHO Building installer
SET NAME=%3
CALL scripts\installer\makesfx.bat "%~dp0release\IntraMaps Roam%NAME% Installer " dist
CALL scripts\installer\makesfx.bat "%~dp0release\IntraMaps Roam%NAME% Installer - Silent" dist -s
GOTO END

:test
@ECHO ON
ECHO Running tests
py.test --cov=src\roam src\roam.tests --cov-report html --cov-report term
GOTO END

:test-only
ECHO Running tests
py.test src\roam.tests
GOTO END


:END
popd
