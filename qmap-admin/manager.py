import PyQt4.uic
from PyQt4.QtCore import QAbstractItemModel, Qt, QString
from PyQt4.QtGui import (QDialog, QApplication, QListWidgetItem, 
						QStandardItemModel, QStandardItem, QDataWidgetMapper,
						QItemSelectionModel)
import sys
import os
import json

curdir = os.path.abspath(os.path.dirname(__file__))
pardir = os.path.join(curdir, '..')
sys.path.append(pardir)

from src import build

def getForms():
    """ Get all the custom user forms that have been created.
    Checks for "form" at the start to detect module as custom form

    @Returns A list of modules that contain user forms.
    """
    formspath = os.path.join(curdir,'entry_forms')
    for module in os.listdir(formspath):
        if module[:4] == 'form':
            if os.path.exists(os.path.join(formspath,module,"settings.config")):
                yield module

def getProjects():
	projectspath = os.path.join(curdir,'projects')
	for project in os.listdir(projectspath):
		if project.endswith(".qgs"):
			yield project[:-4]

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
		self.populateForms()
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
		forms = settings[QString('forms')]  

		for form in forms:
			formitem = self.formmodel.findItems(form)[0]
		 	formitem.setCheckState(Qt.Checked)

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
		for form in getProjects():
			projectitem = QStandardItem(form)
			projectitem.setCheckable(True)
			self.projectsmodel.insertRow(row, projectitem)
			row += 1

	def populateForms(self):
		row = 0
		for form in getForms():
			formitem = QStandardItem(form)
			formitem.setCheckable(True)
			self.formmodel.insertRow(row, formitem)
			row += 1

if __name__ == "__main__":
	app = QApplication(sys.argv)
	config = build.readTargetsConfig()
	print config
	manager = QMapManager(config)
	manager.show()
	app.exec_()