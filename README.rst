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

|name| is a field data collection application built using QGIS. It was built to be easy to use on (windows) based tablet devices, with Android planned for the future.

Custom forms are built using Qt Designer and follow a convention based approach in order to save configuration.  The general goal of |name| is to be datasource agnostic in most of what it does.  

|name| was orignally built by Southern Downs Regional Council, and now open sourced under the GPL, in order to aid in field data collection. |name| is maintained by `Nathan <https://github.com/NathanW2>`_ at work and in his spare time.


Requirements
-------------
- Latest development QGIS Version (this is due to bug fixes in master)
- mock (optional to run tests)
- Qt Designer (part of the qt4-devel package)

OSGeo4W Packages

- qgis-dev
- qt4-devel

If you need SQL Server syncing support

- MS SQL Server 2008 (express or greater)
- .NET 3.5 (or greater)
- Microsoft Sync Framework

Syncing Support
-----------------
Supported sycning providers

  - MS SQL Server 2008

At the moment syncing of MS SQL 2008 Spatial layers is done using MS SQL Sync Framework.

Syncing support is not a requirement to use QMap, nor is it a requirement to use SQL Server 2008 layers in your projects.  

If syncing support is not needed build.py can take --with-mssyncing=False which will skip the compiling of the .NET syncing library. 

Syncing support for different data sources e.g. PostGIS, SpatiaLite might added later.

Downloading and Running
-----------------------

  - Download the latest version of |name| from 

Program Layout
--------------
There are two parts to |name|.
- The client program
and
- The client manager

Client Program
!!!!!!!!!!!!!!
The client program includes a QGIS plugin, a bootloader to load QGIS using
``--configpath``, and depolyed forms and projects.

The client progam can be depolyed to a client using:

::

    python build.py --target=Touch --with-tests=False deploy
    
with ``Touch`` being defined in targets.ini as:

::

    [Touch]
    client : \\computername\path\to\desktop
    projects : Water.qgs
    forms : formWater
    
See ``/docs/README`` for more information

The client Manager
!!!!!!!!!!!!!!!!!!
The client manager is the side of the program that contains the all depolyable
forms and projects, tools to build the client project, tools to depoly forms
and projects to the client/s.

Forms and projects are stored under ``/project-manager/``. Forms should be added
into the ``/project-manager/entry_forms`` folder and projects into the
``/project-manager/projects/`` folder.  

Project and forms in the ``/project-manager/`` folder can then be used inside
targets.ini to depoly different forms and projects to different clients by running:

::

    python build.py --target=Client1 deploy
    python build.py --target=Client2 deploy
    python build.py --target=Client4 deploy

With ``Client1``, ``Client2``, ``Client4` being different devices with different
forms and projects.

Client Manager and Data
+++++++++++++++++++++++

|name| takes a hands off approach to data management in that it will not manage, 
copy, move, or otherwise touch your project data.  Data should be managed by
the admin of the clients.

The best way to make portable project files is to use a database on the client and
build a project using a mirror of the database on the admins machine, or else you
can use relative paths in the project file.

**Example of using relative paths:**

On admin machine in ``/project-manager/projects`` folder:

::

    myproject.qgs
    data
      |-- layer1.shp
      |-- layer2.shp
      |-- layer3.shp
      |-- rasterlayer.tiff
      
After using:

::

    python build.py --target=Client1 deploy
    
The ``myproject.qgs`` file will be depolyed but not the data. Copy the data into
``{deploypath}/QMap/app/python/plugins/QMap/projects/`` and the project will open
the data using relative paths.  Provided of course that your project file is saved
in QGIS with relative paths.

Running the sample
-------------------

- Download the sample data from https://github.com/downloads/NathanW2/qmap/sample_data.sqlite
- Run make_win.bat in the OSGeo4W shell. Making sure --target is set to Sample.
- Save sample_data.sqlite into ``C:\QMap\app\python\plugins\QMap\projects``
- Lauch QMap.bat from inside ``C:\QMap``
- Load the ``Trees (Sample)`` project from the project list.

License
--------------

|name| is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License version 2 (GPLv2) as
published by the Free Software Foundation.

The full GNU General Public License is available in LICENSE.TXT or
http://www.gnu.org/licenses/gpl.html


Disclaimer of Warranty (GPLv2)
--------------

There is no warranty for the program, to the extent permitted by
applicable law. Except when otherwise stated in writing the copyright
holders and/or other parties provide the program "as is" without warranty
of any kind, either expressed or implied, including, but not limited to,
the implied warranties of merchantability and fitness for a particular
purpose. The entire risk as to the quality and performance of the program
is with you. Should the program prove defective, you assume the cost of
all necessary servicing, repair or correction.


Limitation of Liability (GPLv2)
--------------

In no event unless required by applicable law or agreed to in writing
will any copyright holder, or any other party who modifies and/or conveys
the program as permitted above, be liable to you for damages, including any
general, special, incidental or consequential damages arising out of the
use or inability to use the program (including but not limited to loss of
data or data being rendered inaccurate or losses sustained by you or third
parties or a failure of the program to operate with any other programs),
even if such holder or other party has been advised of the possibility of
such damages.


