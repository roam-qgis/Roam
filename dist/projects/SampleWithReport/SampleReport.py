import os
from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QPushButton
from roam.report import Report
from roam import utils

class SampleReport(Report):
    def __init__(self, folder, config, parent):
        super(SampleReport, self).__init__(folder, config, parent)
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
        self.popJobs()
	self.popInfestations()
	self.popContractors()
	self.connectButtons()

    def popJobs(self):
	self.jobsTable.setRowCount(0)
	""" populate Jobs Table """
	self.dbcur.execute("select job_id, job_date, inspector, territory, job, hours from jobs")
        jlist = self.dbcur.fetchall()
        self.addRows("jobsTable", jlist)
    
    def popInfestations(self):
	self.infestationsTable.setRowCount(0)
	""" populate Infestations Table """
	self.dbcur.execute("select job_id, kind, species, severity from infestations")
        ilist = self.dbcur.fetchall()
        self.addRows("infestationsTable", ilist)

    def popContractors(self):
	self.contractorsTable.setRowCount(0)
	""" populate Contractors Table """
	self.dbcur.execute("select job_id, contractor, hours from contractors")
        clist = self.dbcur.fetchall()
        self.addRows("contractorsTable", clist)

    
    def addRows(self, tablename, rows):
        for ridx, row in enumerate(rows):
	    self.tables[tablename].insertRow(ridx)
	    for cidx, cell in enumerate(row): 
                self.tables[tablename].setItem(ridx, cidx, QTableWidgetItem(str(cell)))
  
    def connectButtons(self):
	self.deleteJob.pressed.connect(self.deletejob)
	self.deleteInfestation.pressed.connect(self.deleteinfestation)
	self.deleteContractor.pressed.connect(self.deletecontractor)
	self.commitButton.pressed.connect(self.saveChanges)

    def saveChanges(self):
	self.savejobs()
	self.saveinfestations()
	self.savecontractors()
	#self.dbcur.commit()
	
    def savejobs(self):
	for x in range(0, self.jobsTable.rowCount()):
            job_id = self.jobsTable.item(x, 0).text()
	    date = self.jobsTable.item(x, 1).text()
	    inspector = self.jobsTable.item(x, 2).text()
	    territory = self.jobsTable.item(x, 3).text()
	    job = self.jobsTable.item(x, 4).text()
	    hours = self.jobsTable.item(x, 5).text()
	    sql = u"update jobs set job_date = \'{}\', territory = \'{}\', inspector = \'{}\', job = \'{}\',  hours = \'{}\' where job_id = \'{}\')".format(date, inspector, territory, job, hours, job_id)
	    self.dbcur.execute(u"select * from jobs")
	self.popJobs()

    def deletejob(self):
	x = self.jobsTable.currentRow()
	job_id = self.jobsTable.item(x,0).text()
	self.removeCurrentRow("jobsTable")
	sql = u"delete from jobs where job_id = \'{}\'".format(job_id)
	self.dbcur.execute(sql)
	self.popJobs()
	self.popInfestations()
	self.popContractors()

    def saveinfestations(self):
	pass

    def deleteinfestation(self):
	self.removeCurrentRow("infestationsTable")

    def savecontractors(self):
	pass

    def deletecontractor(self):
	self.removeCurrentRow("contractorsTable")

    def removeCurrentRow(self, tablename):
        self.tables[tablename].removeRow(self.tables[tablename].currentRow())
