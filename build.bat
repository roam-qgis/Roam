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
python setup.py build_roam
GOTO END

:clean
SET OLD_CLEAN=%CLEAN%
SET CLEAN=YES
python setup.py clean
SET CLEAN=%OLD_CLEAN%
GOTO END

:release
ECHO Building release
python setup.py build_roam
GOTO zip

:zip
IF NOT EXIST release MKDIR release
del %BASE%release\*.* /Q /F
pushd build\exe.win-amd64-3.7
ECHO %CD%
ECHO Making zip file..
SET NAME=%2
python -m zipfile -c "%BASE%\release\Roam%NAME%.zip" .
GOTO END

:installer
ECHO Building installer
SET NAME=%2
CALL %BASE%scripts\installer\makesfx.bat "%BASE%release\Roam%NAME% Installer " build\exe.win-amd64-3.7
CALL %BASE%scripts\installer\makesfx.bat "%BASE%release\Roam%NAME% Installer - Silent" build\exe.win-amd64-3.7 -s
GOTO END

:inno_installer
ECHO Building installer
SET NAME=%2
set path="C:\Program Files (x86)\Inno Setup 6";%path%
iscc /F"Roam%NAME% Installer" %BASE%scripts\installer\roam-installer.iss 
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
