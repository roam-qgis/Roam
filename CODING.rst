================================
IntraMaps Roam Code Layout
================================

IntraMaps Roam is built as a QGIS plugin that runs in a QGIS sandbox in order to feel like a tablet friendly version of
QGIS.  This document outlines the layout of the code and how to build a Roam application deployment.

    - src - Contains the src code for the Roam application itself.
    - projects - Contains a folder for each Roam project.  Some of these are generic and some are client projects.
    - installer - Contains source code to generate a self extracting zip installer
    - docs - Contains generic IntraMaps Roam help manual.
    - admin - Contains build scripts and export methods to creating a Roam bundle

Generated folders.

    - export - Final output after export script has been run
    - build - Application build location

The above folders can be deleted and will be recreated when any of the build scripts are run.

Export Scripts
-------------------------------

``admin\exports`` contains a bunch of export scripts for different project setups.  Each Roam deployment can be different
so different scripts are used to export just what is needed for that setup.

An example export script is::

    @ECHO OFF

    SET NAME=Busselton Install

    call baseexport.bat

The ``NAME`` variable must be set in order to export the right projects for the deployment.  These settings are found in
``targets.config``. An example config is::

    clients:
        Busselton Install:
            path : ..\export\Busselton Install
            projects:
                - busselton_firebreak

All config files in Roam use YAML as the format.  YAML is sensitive to tab so always use space when indenting

Roam deployments can also be bundled into a self extracting installer.  This is done using one of the ``bundle_xxx`` batch
files.  A example of a bundle batch file is::

    call export_busselton.bat
    call %~dp0bundle.bat

This will call the ``export_busselton.bat`` file and then call the bundle process.  The bundle process takes the output
for the deployment in export and creates a self extracting zip file.

The build process
-------------------------------------
The build process is done using Python (fabricate) and batch files.  All the build logic is inside ``admin\build.py``
and is kept as simple as possible.  Most of ``build.py`` takes care of copying the src files out to the build folder and
then moving the project into the export folder for that setup.












