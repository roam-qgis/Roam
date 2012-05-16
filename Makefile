#/***************************************************************************
# SDRCDataCapture
# 
# Prototype Data collection software for SDRC
#                             -------------------
#        begin                : 2012-03-21
#        copyright            : (C) 2012 by Nathan Woodrow @ SDRC
#        email                : nathan.woodrow@southerndowns.qld.gov.au
# ***************************************************************************/
# 
#/***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************/

# Makefile for a PyQGIS plugin 

PLUGINNAME = sdrcdatacapture

PY_FILES = sdrcdatacapture.py __init__.py

EXTRAS = icon.png 

UI_FILES = ui_listmodules.py

RESOURCE_FILES = resources.py

compile:	$(UI_FILES)	$(RESOURCE_FILES)

%.py:	%.qrc
	pyrcc4 -o $@ $<

%.py:	%.ui
	@C:\OSGeo4w\bin\python.exe C:\OSGeo4w\apps\Python27\Lib\site-packages\PyQt4\uic\pyuic.py -o $@ $<

# The deploy  target only works on unix like operating system where
# the Python plugin directory is located at:
# $HOME/.qgis/python/plugins
deploy: compile
	@mkdir -p deply/app/
# cp -vf $(PY_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
# cp -vf $(UI_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
# cp -vf $(RESOURCE_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
# cp -vf $(EXTRAS) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)

# Create a zip package of the plugin named $(PLUGINNAME).zip. 
# This requires use of git (your plugin development directory must be a 
# git repository).
# To use, pass a valid commit or tag as follows:
#   make package VERSION=Version_0.3.2
# package:  compile
	# rm -f $(PLUGINNAME).zip
	# git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
	# echo "Created package: $(PLUGINNAME).zip"
