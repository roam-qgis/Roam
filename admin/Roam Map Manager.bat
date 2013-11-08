call %~dp0setenv.bat

"%OSGEO4W_ROOT%\bin\qgis-dev.bat" --configpath %~dp0mapmanager --optionspath %~dp0mapmanager %*
