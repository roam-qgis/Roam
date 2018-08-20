@ECHO OFF
REM ---------------------------------------------------------------------------------------

REM Script to install the needed dev tools into the Python install that comes with OSGeo4W
REM Change %OSGEO4W_ROOT% in setenv.bat to change in the install folder.

REM ---------------------------------------------------------------------------------------

pushd %~dp0
CALL setenv.bat %1
CALL "%OSGEO4W_ROOT%\bin\o4w_env.bat"

python -m pip install -r ..\requirements.txt
GOTO END

:END
pause
