@ECHO OFF
call %~dp0setenv.bat
START %OSGEO4W_ROOT%\bin\designer.exe
