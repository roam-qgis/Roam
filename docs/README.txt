====================
QGIS Data Collection
====================

.. contents::
.. sectnum::

Installing
----------

Conventions
-----------
QGIS Data collection follows a convention over configuration style.

Layer field names map to object names in Qt form (.ui)

Images saved from drawing pad are stored in data\{layername}\images.
Images have the following convention:

    {id}_{fieldname}.jpg

Temp images that are saved before commit have the following convention:

    drawingFor_{fieldname}.jpg

drawingFor\_ is replaced with {id} when commited and moved into the images folder.

