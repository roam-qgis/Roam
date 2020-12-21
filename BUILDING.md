BUILDING
===============================

Setting up build
------------------------------

You only need to do this step once.

You need:

- [QGIS 3.*] https://qgis.org/downloads/QGIS-OSGeo4W-3.10.12-1-Setup-x86_64.exe
- On installation ensure python3-pip is selected to be installed
- If building an installer either WinRAR or InnoSetup are required.

1. Run cmd.exe as admin
2. ``build.bat install-req``

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
    - inno_installer
    - test
    - test-only

1. Building ui files
-----------------------

If you change any of the .ui files you need to run the following command to regenerate the generated ui files.

``build.bat build``

``build.bat`` is a make file with commands to build and package Roam

2. Creating Exe
----------------------

Only supported on Windows.  Uses cx_Freeze to build the final exe and bundle all files together.

Creates the  `Roam.exe` file in the `\dist` folder.  Also builds a release zip file in the `\release` folder.

``build.bat exe`` or ``build.bat release``

3. Making installer package
----------------------

An installer package can be made using the `installer` or `inno_installer` commands depending on the software available. Will create a installer exe release.

``build.bat installer`` or ``build.bat inno_installer``
