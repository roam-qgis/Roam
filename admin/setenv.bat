@ECHO OFF

SET OSGEO4W_ROOT=C:\OSGeo4W

PATH=%OSGEO4W_ROOT%\bin;%PATH%
for %%f in ("%OSGEO4W_ROOT%\etc\ini\*.bat") do call "%%f"