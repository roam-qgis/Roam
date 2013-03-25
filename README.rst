====================
|name| - README
====================

:Authors:
    Nathan Woodrow,
    Damien Smith

:Version: 2.0

.. |name| replace:: QMap
.. |f| image:: images/folder.png

.. contents::

|name| is a field data collection application built using QGIS. It was built to be easy to use on (windows) based tablet devices, with Android planned for the future.

Custom forms are built using Qt Designer and follow a convention based approach in order to save configuration.  The general goal of |name| is to be datasource agnostic in most of what it does.  

|name| was orignally built by Southern Downs Regional Council, and now open sourced under the GPL, in order to aid in field data collection. |name| is maintained by `Nathan <https://github.com/NathanW2>`_ at work and in his spare time.


Requirements
-------------
- QGIS 2.0 (latest dev build from OSGeo4W)
- Qt Designer (part of the qt4-devel package)
- Microsoft Sync Framework (http://www.microsoft.com/en-us/download/details.aspx?id=23217)

OSGeo4W Packages

- qgis-dev
- qt4-devel

If you need SQL Server syncing support

- MS SQL Server 2008 (express or greater)
- .NET 3.5 (or greater)
- Microsoft Sync Framework (http://www.microsoft.com/en-us/download/details.aspx?id=23217)

Projects
-------------------
QMap projects are stuctured using a single folder in the qmap-admin/projects folder and deployed
to the device using QMap Admin tool.

Project stucture is as follows:

::

	---projects
	    +---Project Name
	        |   splash.png
	        |   your project.qgs
	        |
	        +---layername
	        |   |   form.ui
	        |   |   icon.png
	        |   |
	        |   \---help
	        |           column1.html
	        |           column2.html
	        |           column3.html
	        |
	        \---_data
	                {extra data your project needs}
	               
	                
Each project folder must contain a `splash.png`, and a `.qgs` project. One one `.qgs` file is
supported per project.

Every folder inside the project folder will be treated as an editing layer, the 
name of the folder must match the name in the .qgs project file.  Each layername folder
may contain a `icon.png` which will be used on the toolbar, and a help folder which
contains a html file for each column.

`help` folders are optional.  Any folders starting with _ will be ignored by QMap but still
copied to the device. 

An example project layout is:

::

	---projects
	    +---Firebreak Inspection
	    |   |   fireinspect.qgs
	    |   |   splash.png
	    |   |
	    |   +---Inspection
	    |   |       fireform.ui
	    |   |       icon.png
	    |   
	    |   
	    |   
	    |   
	    |
	    \---Trees (Sample)
	        |   splash.png
	        |   Trees (Sample).qgs
	        |
	        +---trees
	        |   |   form.ui
	        |   |   icon.png
	        |   |
	        |   \---help
	        |           Asset_Type.html
	        |           Condition.html
	        |           Species.html
	        |
	        \---_data
	                sample_data.sqlite

QMap Layers
--------------

Layers in QMap are defined using plain folders inside the project folder. 
	
	.. note::
	
	Each layer folder must match the name of the layer in the QGIS project.  

When QMap loads a project it will match each folder name and assign it to the QGIS
layer of the same name.  QMap will create a new button on the toolbar for each matching
layer in the project folder.

The form that QMap will use for each layer is defined 
in the normal QGIS project using the `Fields` tab. The options are `Autogenerate`, `Drag and Drop`,
`UI-File`. If using the UI-File option the `.ui` file used should be located in layer folder as per
the example.

Syncing Support
-----------------
Current supported sycning providers

- MS SQL Server 2008

At the moment syncing of MS SQL 2008 Spatial layers is done using MS SQL Sync Framework.

Syncing support is not a requirement to use QMap, nor is it a requirement to use 
SQL Server 2008 layers in your projects.

Syncing support for different data sources e.g. PostGIS, SpatiaLite might added later.

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


