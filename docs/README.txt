====================
|name|
====================

:Authors:
    Nathan Woodrow,
    Damien Smith

:Version: 1.0

.. |name| replace:: QGIS Data Collector



The |name| is a simple to use, simple to configure, data collection
<<<<<<< HEAD
program built by Southern Downs Regional Council that uses QGIS and its Python
plugin model as a base.  |name| is a QGIS Python plugin that removes most of the
interface and replaces it with a simple to use interface for data collection.
=======
program built by Southern Downs Regional Council that uses QGIS.  |name| is a QGIS
Python plugin that removes most of the interface and replacing it with a simple
to use interface for data collection.
>>>>>>> Add some install notes

As |name| is just a Python plugin you can use your normal QGIS project files (.qgs)
in order to create mapping projects.

Requirements
-------------
- Latest QGIS Version > 1.8
- MS SQL Server 2008 (express or greater)
- .NET 3.5 (or greater)
- Microsoft Sync Framework
- Qt Designer (for form building)
- Something to install this on (some kind of fancy tablet PC)

Building
----------

For building we use fabricate_ which is a build tool written in pure Python,
because frankly GNUMake is a pain to use, the syntax is just plain strange,
and it sucks at error reporting.

.. _fabricate: http://code.google.com/p/fabricate/

To build just run **make_win.bat** from the main root folder.  build.py will generate
all the needed files and deploy them into the build directory.

The QGIS plugin location is /build/app/python/plugins

You can run build.py using Python:

.. code-block:: console

    #Clean build files
    python build.py clean

    #Build only docs
    python build.py docs
     
    #Build only
    python build.py build

The version number used is {year}.{month}.{day}.{commitid} and the version in
metadata.txt is the version number for all the files and related binaries in the
project.

.. contents::
.. sectnum::


Installing
----------

.. note:: If you haven't done so already please see Building_ before
          installing

- Install
    - MS SQL Server 2008
    - .NET 3.5
    - Microsoft Sync Framework
    - QGIS

Copy the build folder into the

Conventions
-----------

|name| follows a convention over configuration style in order to
make setup consistant and easy. At times we still will need to configure things
but this will be kept to a minimum.

Form Conventions
++++++++++++++++

- Layer field names map to object names in Qt form (.ui)

  The form binder searchs the form for a widget named the same as the field and
  will bind and unbind the value from the database to the form.  The widget type
  defines how the object is bound e.g. a char column named *MyColumn* will bind
  to the QLineEdit::text() property correctly of the widget with the same name.

  .. warning:: There is very little error handling with the form binding.
               Binding a char column with the value "Hello World" to a QCheckBox
               might do strange things.

- In order to create the correct date picker dialog we first look for a DateTimePicker
  then we get its parent - which will be a layout - then look for a PushButton that
  we can use to open the dialog with.

  .. figure:: DateTimePickerExample.png

     Example of what the correct widget layout in order to get a date time picker.

  .. figure:: DateTimePickerExampleLayout.png

     Layout for date time picker

  A correctly bound date time picker button has a the word "Pick" and a icon when
  opening the dialog.

  .. figure:: DateTimePickerBound.png

     Result of correct binding

- To correctly create a drawing pad button binding do the following:
    - Create a field in the datebase
    - Name a QPushButton with the field name - following the "fieldnames = object name"
      convention.
    - Label the button with "Drawing"

  .. figure:: DrawingBound.png

     Result of correct drawing button binding

  .. note:: The image is stored on the filesystem not in the layer. So no value is
           ever stored in the database. See `Program Conventions`_ for details on
           image convention.


Program Conventions
+++++++++++++++++++

- Images saved from drawing pad are stored in data\\{layername}\\images.
  Images have the following naming convention:

        {id}_{fieldname}.jpg

  Example:

        D896C1C0-9E4B-11E1-AB3F-002564CC69E0_Drawing.jpg

  Temp images that are saved before commit have the following convention and are
  saved in the user temp directory:

        drawingFor_{fieldname}.jpg

  *drawingFor\_* is replaced with *{id}* when the record is commited into the layer.
  The image is then moved into the images folder.

- Projects are stored in the projects\\ directory.  The name of the .qgs file will
  be used in the open project dialog box.  The project directory is **not** recursive

SQL Table Conventions
+++++++++++++++++++++
In order for syncing to be correctly setup the table must contain the following
columns:

    UniqueID as uniqueidentifier

    Primary Key column **must** be Int

Creating a new form
-------------------