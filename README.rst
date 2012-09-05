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

|name| is a simple to use, simple to configure, data collection
program built by Southern Downs Regional Council that uses QGIS.  |name| is a QGIS
Python plugin that removes most of the interface and replacing it with a simple
to use interface for data collection. The program is only in early alpha stage 
but is functional and activly worked on.

At the current time it is implmented as a QGIS Python plugin and is aimed 
at Windows, however it wouldn't take much to change it into a standalone 
QGIS program and run on any platform.

Although this project is written as a QGIS plugin it is designed to be run 
in in it's own QGIS sandbox using the --config path command line option of QGIS. 
This means that it acts like a standalone program and will store its settings 
away from the normal QGIS install. This is to provide a controlled QGIS 
environment with a minimal interface

As |name| is just QGIS you can use your normal QGIS project files (.qgs)
in order to create mapping projects. Forms are loaded based 
on the naming of layers in the project.  E.g. A form can be bound to the 
layer "Sewer Main" and will be useable in any project that includes 
a layer with the name "Sewer Main". Note QGIS allows you rename layers without
renaming the underlying file name.

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

    python build.py --target=Client1 --with-tests=False deploy
    python build.py --target=Client2 --with-tests=False deploy
    python build.py --target=Client4 --with-tests=False deploy

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

    python build.py --target=Client1 --with-tests=False deploy
    
The ``myproject.qgs`` file will be depolyed but not the data. Copy the data into
``{deploypath}/QMap/app/python/plugins/QMap/projects/`` and the project will open
the data using relative paths.  Provided of course that your project file is saved
in QGIS with relative paths.

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


