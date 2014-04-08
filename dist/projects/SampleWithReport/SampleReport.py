import os
from PyQt4.QtCore import Qt
from PyQt4.QtGui import  QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
from roam.report import Report
from roam import utils

class SampleReport(Report):
    def __init__(self, folder, config, errorbar, parent=None):
        super(SampleReport, self).__init__(folder, config, errorbar, parent)
	self.tables = {}
	self.dbpath = os.path.join(folder, "data", "sampledata.sqlite")
	self.db = None
	import sqlite3
	try:
	    self.db = sqlite3.connect(self.dbpath)
	    self.dbcur = self.db.cursor()
	except sqlite3.Error, e:
            raise


    def uisetup(self):
	self.tables = {"jobsTable": self.jobsTable,
			"contractorsTable": self.contractorsTable,
	                "infestationsTable": self.infestationsTable
		      }
	self.contractorsTable.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.popJobs()
	self.popInfestations()
	self.popContractors()
	self.connectButtons()
	

    def popJobs(self):
	self.jobsTable.setRowCount(0)
	""" populate Jobs Table """
	self.dbcur.execute("select job_id, job_date, inspector, territory, job, hours from jobs")
        jlist = self.dbcur.fetchall()
        self.addRows("jobsTable", jlist, True, False)
    
    def popInfestations(self):
	self.infestationsTable.setRowCount(0)
	""" populate Infestations Table """
	self.dbcur.execute("select id, job_id, kind, species, severity from infestations")
        ilist = self.dbcur.fetchall()
        self.addRows("infestationsTable", ilist, True, True)

    def popContractors(self):
	self.contractorsTable.setRowCount(0)
	""" populate Contractors Table """
	self.dbcur.execute("select id, job_id, contractor, hours from contractors")
        clist = self.dbcur.fetchall()
        self.addRows("contractorsTable", clist, True, True)

    
    def addRows(self, tablename, rows, ro1=False, ro2=False):
        for ridx, row in enumerate(rows):
	    self.tables[tablename].insertRow(ridx)
	    for cidx, cell in enumerate(row):
		item = QTableWidgetItem(str(cell))
		if (cidx == 0 and ro1) or (cidx == 1 and ro2):
		    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                self.tables[tablename].setItem(ridx, cidx, item)
        self.tables[tablename].resizeColumnsToContents()

  
    def connectButtons(self):
	self.deleteJob.pressed.connect(self.deletejob)
	self.deleteInfestation.pressed.connect(self.deleteinfestation)
	self.deleteContractor.pressed.connect(self.deletecontractor)
	self.commitButton.pressed.connect(self.saveChanges)

    def saveChanges(self):
	self.savejobs()
	self.saveinfestations()
	self.savecontractors()
	self.db.commit()
	self.popInfestations()
        self.popContractors()
        self.popJobs()
	self.bar.pushMessage("Saved Changes")

    def savejobs(self):
	for x in range(0, self.jobsTable.rowCount()):
            job_id = self.jobsTable.item(x, 0).text()
	    date = self.jobsTable.item(x, 1).text()
	    inspector = self.jobsTable.item(x, 2).text()
	    territory = self.jobsTable.item(x, 3).text()
	    job = self.jobsTable.item(x, 4).text()
	    hours = self.jobsTable.item(x, 5).text()
	    sql = u"update jobs set job_date = \'{}\', territory = \'{}\', inspector = \'{}\', job = \'{}\',  hours = \'{}\' where job_id = \'{}\'".format(date, inspector, territory, job, hours, job_id)
	    self.dbcur.execute(sql)

    def deletejob(self):
	row = self.jobsTable.currentRow()
	job_id = self.jobsTable.item(row,0).text()
	self.jobsTable.removeRow(row)
	sql = u"delete from infestations where job_id = \'{}\'".format(job_id)
	self.dbcur.execute(sql)
	sql = u"delete from contractors where job_id = \'{}\'".format(job_id)
	self.dbcur.execute(sql)   
	sql = u"delete from jobs where job_id = \'{}\'".format(job_id)
	self.dbcur.execute(sql)
	self.popJobs()
	self.popInfestations()
	self.popContractors()

    def saveinfestations(self):
	for x in range(0, self.infestationsTable.rowCount()):
            iid = self.infestationsTable.item(x, 0).text()
	    kind = self.infestationsTable.item(x, 2).text()
	    species = self.infestationsTable.item(x, 3).text()
	    severity = self.infestationsTable.item(x, 4).text()
	    sql = u"update infestations set kind = \'{}\', species = \'{}\', severity = \'{}\' where id = \'{}\'".format(kind, species, severity, iid)
	    self.dbcur.execute(sql)


    def deleteinfestation(self):
	row = self.infestationsTable.currentRow()
	id = self.infestationsTable.item(row, 0).text()
	self.infestationsTable.removeRow(row)
	sql = u"delete from infestations where id = \'{}\'".format(id)
        self.dbcur.execute(sql)
	self.popInfestations()

    def savecontractors(self):
	for x in range(0, self.contractorsTable.rowCount()):
            iid = self.contractorsTable.item(x, 0).text()
	    contractor = self.contractorsTable.item(x, 2).text()
	    hours = self.contractorsTable.item(x, 3).text()
	    sql = u"update contractors set contractor = \'{}\', hours = \'{}\' where id = \'{}\'".format(contractor, hours, iid)
	    self.dbcur.execute(sql)


    def deletecontractor(self):
	row = self.contractorsTable.currentRow()
	id = self.contractorsTable.item(row, 0).text()
	self.contractorsTable.removeRow(row)
	sql = u"delete from contractors where id = \'{}\'".format(id)
	self.popContractors()
        self.dbcur.execute(sql)
	self.popContractors()
