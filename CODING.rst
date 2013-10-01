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
so different scripts are used to export just what is needed.

An example export script is::

    @ECHO OFF

    SET NAME=Busselton Install

    call baseexport.bat

    REM SET PROJECT=%HOME%\projects\Busselton Install
    REM move /Y "%PROJECT%\_docs\*" "%HOME%\docs\"

The ``NAME`` variable must be set in order to export the right projects for the deployment.  These settings are found in
``targets.config`` an example config is::

    clients:
        Busselton Install:
            path : ..\export\Busselton Install
            projects:
                - busselton_firebreak

All config files in Roam use YAML as the format.  YAML is sensitive to tab so always use space when indenting

Creating an installer
-------------------------------
