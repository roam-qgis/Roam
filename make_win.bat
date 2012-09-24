@ECHO OFF
set PYTHONPATH=C:\OSGeo4W\apps\qgis-dev\python
Set PATH=C:\OSGeo4W\apps\qgis-dev\bin;%PATH%
set QGISHOME=C:\OSGeo4W\apps\qgis-dev\

python build.py --target=Sample --with-tests=False deploy
pause
