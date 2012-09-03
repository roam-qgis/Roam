====================
|name| - README
====================

:Authors:
    Nathan Woodrow,
    Damien Smith

:Version: 1.0

.. |name| replace:: QMap
.. |f| image:: images/folder.png


.. contents::
.. sectnum::

|name| is a simple to use, simple to configure, data collection
program built by Southern Downs Regional Council that uses QGIS.  |name| is a QGIS
Python plugin that removes most of the interface and replacing it with a simple
to use interface for data collection. The program is only in early alpha stage 
but is functional and activly worked on.

At the current time it is implmented as a QGIS Python plugin and is aimed 
at Windows, however it wouldn't take much to change it into a standalone 
QGIS program and run on any platform.

As |name| is just a QGIS you can use your normal QGIS project files (.qgs)
in order to create mapping projects.

Requirements
-------------
- Latest development QGIS Version (this is due to bug fixes in master)
- nose and mock (for Python tests)
- MS SQL Server 2008 (express or greater)
- .NET 3.5 (or greater)
- Microsoft Sync Framework
- Qt Designer (for form building)
- Something to install it on (some kind of fancy tablet PC)

Syncing
--------------
At the moment syncing is done using MS SQL Sync Framework as it takes away a lot
of the leg work for MS SQL syncing. If syncing support is not needed you can 
just remove the button from the interface and remove the calls to MSBuild 
in build.py.  Later this might become a switch, and/or support for different 
data sources added e.g. PostGIS, SpatiaLite