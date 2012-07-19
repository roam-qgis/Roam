
set PYTHONPATH=C:\OSGeo4W\apps\qgis-dev\python
Set PATH=C:\OSGeo4W\apps\qgis-dev\bin;%PATH%
set QGISHOME=C:\OSGeo4W\apps\qgis-dev\

nosetests tests --with-coverage --cover-html --cover-package=form_binder,syncing
pause