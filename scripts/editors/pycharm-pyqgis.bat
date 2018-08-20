@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to setup the environment for building Roam with QGIS 2.x.
REM This script sets the base folder that is used though out the build process
REM and sets the location to Python.

REM Change %OSGEO4W_ROOT% in setenv.bat to change in the location of QGIS.

REM ---------------------------------------------------------------------------------------


CALL %~dp0..\setenv.bat 2.18 %*

SET PYCHARM="C:\Program Files\JetBrains\PyCharm Community Edition 2017.2.2\bin\pycharm64.exe"

start "PyCharm aware of QGIS" /B %PYCHARM% %*