@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to build the resource and UI files. You only really need to run this if you are
REM running from source.  Package.bat will build all the resources before it creates the package

REM Change %OSGEO4W_ROOT% in setenv.bat to change in the location of QGIS, if necessary.

REM ---------------------------------------------------------------------------------------

pushd %~dp0

SET BASE=%~dp0

call scripts\setenv.bat
IF "%1"=="" goto build
GOTO %1

:watch
python scripts\watchui.py
exit

:install-req
ECHO Installing requirements
python -m pip install -r requirements.txt
python -m pip install libs\py2exe-0.9.3.1-cp37-none-win32.whl
GOTO END

:install-req-build-server
ECHO Installing requirements
python -m pip install -r requirements-tcbuild.txt
GOTO END

:build
ECHO Building..
python setup.py clean
python setup.py build_qt
GOTO END

:exe
ECHO Making package..
python setup.py clean
python setup.py build_qt
python setup.py build
GOTO END

:clean
SET OLD_CLEAN=%CLEAN%
SET CLEAN=YES
python setup.py clean
SET CLEAN=%OLD_CLEAN%
GOTO END

:release
ECHO Building release
python setup.py clean
python setup.py build_qt
python setup.py build
IF NOT EXIST release MKDIR release
del release\*.* /Q /F
pushd dist
ECHO Making zip file..
SET NAME=%2
python -m zipfile -c "..\release\IntraMaps Roam%NAME%.zip" .
GOTO END

:installer
ECHO Building installer
SET NAME=%2
CALL scripts\installer\makesfx.bat "%~dp0release\IntraMaps Roam%NAME% Installer " dist
CALL scripts\installer\makesfx.bat "%~dp0release\IntraMaps Roam%NAME% Installer - Silent" dist -s
GOTO END

:test
@ECHO ON
ECHO Running tests
pytest --cov=src\roam src\roam_tests --cov-report html --cov-report term
GOTO END

:test-only
ECHO Running tests
pytest src\roam_tests
GOTO END

:design
ECHO Opening desinger
START designer.exe
GOTO END

:api-docs
pdoc --html .\src\roam\
GOTO END

:cmd
cmd
GOTO END

:help
ECHO ===========================
ECHO        OPTIONS
ECHO ===========================
ECHO build
ECHO build build
ECHO build exe
ECHO build release
ECHO build test
ECHO build test-only
ECHO build design
ECHO build release 2.7.2
GOTO END

:END
popd
