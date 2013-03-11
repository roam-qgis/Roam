import PyQt4.uic
from PyQt4.QtCore import QAbstractItemModel, Qt, QString
from PyQt4.QtGui import (QDialog, QApplication, QListWidgetItem, 
						QStandardItemModel, QStandardItem, QDataWidgetMapper,
						QItemSelectionModel)
import sys
import os
import json
import glob

curdir = os.path.abspath(os.path.dirname(__file__))
pardir = os.path.join(curdir, '..')
sys.path.append(pardir)

from src import build

from collections import namedtuple

Project = namedtuple('Project', 'name file splash folder')

def getProjects():
	projectpath = os.path.join(curdir, 'projects')
	folders = (sorted( [os.path.join(projectpath, item) 
                       for item in os.walk(projectpath).next()[1]]))
    
	for folder in folders:
	    # The folder name is the display name
	    # Grab the first project file
	    # Look for splash.png
	    # Path to project folder.
	    name = os.path.basename(folder)
	    try:
	        projectfile = glob.glob(os.path.join(folder, '*.qgs'))[0]
	    except IndexError:
	        log("No project file found.")
	        continue
	    try:
	        splash = glob.glob(os.path.join(folder, 'splash.png'))[0]
	    except IndexError:
	        splash = ''
	    
	    yield Project(name, projectfile, splash, folder )

class QMapManager(QDialog):
	def __init__(self, config, parent=None):
		QDialog.__init__(self, parent)
		curdir = os.path.abspath(os.path.dirname(__file__))
		PyQt4.uic.loadUi(os.path.join(curdir,'manager.ui'), self)
		self.model = QStandardItemModel()
		self.projectsmodel = QStandardItemModel()
		self.formmodel = QStandardItemModel()
		self.projectlist.setModel(self.projectsmodel)
		self.formlist.setModel(self.formmodel)
		self.clientlist.setModel(self.model)
		self.clientlist.selectionModel().selectionChanged.connect(self.update)
		self.installbutton.pressed.connect(self.installToClient)
		self.mapper = QDataWidgetMapper()
		self.mapper.setModel(self.model)
		self.mapper.addMapping(self.installpath, 1)
		self.config = config
		self.populateProjects()
		self.populateClients()
		
	def installToClient(self):
		index = self.clientlist.selectionModel().currentIndex()
		item = self.model.itemFromIndex(index)
		print "Deploying to " + item.text()
		build.deployTargetByName(str(item.text()))

	def update(self, selected, deselected ):
		index = selected.indexes()[0]
		self.mapper.setCurrentModelIndex(index)
		item = self.model.itemFromIndex(index)
		settings = item.data().toPyObject()

		for row in xrange(0,self.projectsmodel.rowCount()):
			index = self.projectsmodel.index(row, 0)
			item = self.projectsmodel.itemFromIndex(index)
			item.setCheckState(Qt.Unchecked)

		projects = settings[QString('projects')]
		
		for project in projects:
			project = project[:-4]
			projectitem = self.projectsmodel.findItems(project)[0]
		 	projectitem.setCheckState(Qt.Checked)
				

	def populateClients(self):
		row = 0
		for client, settings in self.config['clients'].iteritems():
			name = QStandardItem(client)
			name.setData(settings)
			path = QStandardItem(settings['path'])
			self.model.insertRow(row, [name, path])
			row += 1

	def populateProjects(self):
		row = 0
		for project in getProjects():
			projectitem = QStandardItem(project.name)
			projectitem.setCheckable(True)
			self.projectsmodel.insertRow(row, projectitem)
			row += 1

if __name__ == "__main__":
	app = QApplication(sys.argv)
	config = build.readTargetsConfig()
	print config
	manager = QMapManager(config)
	manager.show()
	app.exec_()