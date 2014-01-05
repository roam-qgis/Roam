BUILDING
===============================

You need:

- Visual Studio C++ 2008 (http://download.microsoft.com/download/A/5/4/A54BADB6-9C3F-478D-8657-93B3FC9FE62D/vcsetup.exe)
    (This is for the Python compiler for py2exe)
- QGIS 32bit OSGeo4W (http://download.osgeo.org/osgeo4w/osgeo4w-setup-x86.exe)

NOTE: Build scripts assume OSGeo4W install path.

INSTALL NOTE:  If you get a ValueError when running python setup.py install sometimes it can't run the visual studio batch
file.  Simply run C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\Tools\vsvars32.bat in the shell
before running setup.py

1. Download and install Visual Studio C++ Express
2. Run setupdev.bat

setdev.bat will download and install py2exe.  If that fails follow the instructions below.

1. Download py2exe
2. Extract
3. Run OSGeo4W.bat in QGIS install folder
4. CD to exracted folder
5. run: python setup.py install
6. CD back to source folder.

PACKAGING
======================

1. Run package.bat
2. Errors will be in the shell, everything else in package.log
3. Output will be in dist\
