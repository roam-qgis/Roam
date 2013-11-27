====================
|name| - INSTALL
====================


.. |name| replace:: QMap
.. |f| image:: images/folder.png

.. contents::

Admin Setup
-----------

- Install QGIS 2.0 (qgis-dev) using OSGeo4W
- Install qt4-devel
- Download the latest version of |name| from https://github.com/NathanW2/qmap/tags 
  using the Source Code(.zip).
- Extact source files
- Install MS Sync Framework from (http://www.microsoft.com/en-us/download/details.aspx?id=23217)
- Configure devices in ``qmap-admin\\targets.config`` using the following syntax:

	:: 
	
	{
		"clients": {
			"Device Name 1": {
				"path" : "{install path}",
				"projects" : [{list of projects}]
			},
			"Example Device": {
				"path" : "C:\",
				"projects" : ["Trees (Sample)", "Firebreak Inspection"]
			}
		}
	}
	
	targets.config is in JSON format and follows the Python ``json`` module for syntax.

Client Setup
------------

- Install QGIS 2.0 (qgis-dev) using OSGeo4W

Installing to Device
--------------------

- Run ``QMap Admin.bat``
- Select device from the Device lists
- Click Install

Running QMap on the Device
--------------------------

- Navigate to QMap installed location
- Run ``QMap.bat``

Running the sample
-------------------

- Run ``QMap Admin.bat``
- Select ``Trees (Sample)`` from the Device lists
- Click Install
- Run ``QMap.bat`` on the device from ``C:\\``

