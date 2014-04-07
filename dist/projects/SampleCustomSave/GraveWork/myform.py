# -*- coding: utf-8 -*-

import os, sys

from PyQt4.QtGui import QDateTimeEdit
from PyQt4.QtCore import Qt
from roam.api import FeatureForm
from roam import utils

class MyForm(FeatureForm):

   def __init__(self, form, *args, **kwargs):
      super(MyForm, self).__init__(form, *args, **kwargs)
      self.dbpath = os.path.join(form.folder, "..", "_data", "sample.sqlite")
      self.db = None
      import sqlite3
      try:
         self.db = sqlite3.connect(self.dbpath)
	 self.dbcur = self.db.cursor()
      except sqlite3.Error, e:
         raise

   def init_form(form):
      form.registerform(BDEForm)

   def uisetup(self):

      """ Get required feature and layer data """

      # taetigkeit kategorie
      # kennung (gewaesser), gm_nr (gwm)
      self.grave_label.setText("Work done on Grave {}, Name {}".format(self.feature["id"], self.feature["name"]))

   def featuresaved(self, feature, values):

      """ export data to gm_daten table """
      job = self.job.currentText()
      date = self.date.dateTime().toString(Qt.ISODate)
      hours = self.hours.text()
      notes = self.notes.toPlainText()
      
      self.dbcur.execute(u"insert into grave_jobs (job, job_date, hours, note) values (?, ?, ?, ?)", 
		[self.job.currentText(),
		 self.date.dateTime().toString(Qt.ISODate), 
		 self.hours.text(), 
		 self.notes.toPlainText()
		])
      
      self.db.commit()
      self.db.close()
      return True

   @property
   def customSave(self):
       return True
  
   @property
   def allpassing(self):
       return True

