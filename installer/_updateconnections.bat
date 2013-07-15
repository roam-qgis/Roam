@ECHO OFF
: Set to the address of the local and remote server
Set REMOTESERVER=
Set LOCALSERVER=


SET OSGEO4W_ROOT=C:\OSGeo4W
PATH=%OSGEO4W_ROOT%\bin;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
SET PATH=%PATH%;%OSGEO4W_ROOT%\apps\Python27\Scripts

python "%~dp0_install\postinstall.py" %REMOTESERVER% %LOCALSERVER%
pause
