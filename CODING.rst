================================
IntraMaps Roam Code Layout
================================

IntraMaps Roam is built as a QGIS plugin that runs in a QGIS sandbox in order to feel like a tablet friendly version of
QGIS.  This document outlines the layout of the code and how to build a Roam application deployment.

    - src - Contains the src code for the Roam application itself.
    - installer - Contains source code to generate a self extracting zip installer
    - docs - Contains generic IntraMaps Roam help manual.

Generated folders.

The above folders can be deleted and will be recreated when any of the build scripts are run.


The build process
-------------------------------------
The build process is done using Python (fabricate) and batch files.  All the build logic is inside ``build.py``
and is kept as simple as possible. ``build.py`` will build all the ui and resource files needed.












