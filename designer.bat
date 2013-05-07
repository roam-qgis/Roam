@echo off
rem Root OSGEO4W home dir to the same directory this script exists in
set OSGEO4W_ROOT=C:\OSGeo4W
rem Convert double backslashes to single
set OSGEO4W_ROOT=%OSGEO4W_ROOT:\\=\%
echo. & echo OSGEO4W home is %OSGEO4W_ROOT% & echo.

set PATH=%OSGEO4W_ROOT%\bin;%PATH%

rem Add application-specific environment settings
for %%f in ("%OSGEO4W_ROOT%\etc\ini\*.bat") do call "%%f"

rem List available o4w programs
rem but only if osgeo4w called without parameters
@echo on
SET PYTHONPATH=src\qmap\qtcontrols;%PYTHONPATH%
SET PYQTDESIGNERPATH=src\qmap\qtcontrols\plugins
START C:\OSGeo4W\bin\designer.exe

