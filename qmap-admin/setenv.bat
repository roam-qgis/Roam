@ECHO OFF

set OSGEO4W_ROOT=C:\OSGeo4W
PATH=%OSGEO4W_ROOT%\bin;%PATH%
for %%f in (%OSGEO4W_ROOT%\etc\ini\*.bat) do call %%f

set PYTHONPATH=C:\OSGeo4W\apps\qgis-dev\python
Set PATH=C:\OSGeo4W\apps\qgis-dev\bin;%PATH%
set QGISHOME=C:\OSGeo4W\apps\qgis-dev\