BUILDING
===============================

Setting up build
------------------------------

You only need to do this step once.

You need:

- [QGIS 2.18] http://qgis.org/downloads/QGIS-OSGeo4W-2.18.22-1-Setup-x86.exe

1. Run cmd.exe as admin
2. ``build.bat 2.18 install-req``

PyCharm
-------------------------

PyCharm can be started with the right environment using `.\scripts\editors\pycharm-pyqgis.bat`.

The path to PyCharm is hard coded in this batch file so might have to copy and adjust for your setup.

Building
---------

`build.bat` is the main build script.

Following commands are supported:

    - install-req
    - build
    - clean
    - design
    - exe
    - release
    - installer
    - test
    - test-only

Building ui files
-----------------------

If you change any of the .ui files you need to run the following command to regenerate the generated ui files.

2. ``build.bat 2.18 build``

``build.bat`` is a make file with commands to build and package Roam

Creating Exe
----------------------

Only supported on Windows.  Uses Py2Exe to build the final exe and bundle all files together.

Creates the  `Roam.exe` file in the `\dist` folder.

2. ``build.bat 2.18 exe``

Making release package
----------------------

A release package can be made using the `release` command. Will create a installer exe and zip file for release.

2. ``build.bat 2.18 release``

