import os

from PyQt4.QtGui import QWidget, QDialog, QMainWindow

from roam import resources_rc

from roam.ui import (ui_projectwidget, ui_listmodules, ui_helpviewer,
                 ui_helppage, ui_datatimerpicker, ui_settings, ui_infodock, ui_mainwindow, ui_sync,
                 ui_dataentrywidget, ui_reportwidget, ui_deletefeature, ui_imageviewer, ui_actionpicker)


project_widget, project_base = ui_projectwidget.Ui_Form, QWidget
modules_widget, modules_base = ui_listmodules.Ui_ListModules, QWidget
helpviewer_widget, helpviewer_base = ui_helpviewer.Ui_HelpViewer, QDialog
helppage_widget, helppage_base = ui_helppage.Ui_apphelpwidget, QWidget
datepicker_widget, datepicker_base = ui_datatimerpicker.Ui_datatimerpicker, QWidget
settings_widget, settings_base = ui_settings.Ui_settingsWidget, QWidget
infodock_widget, infodock_base = ui_infodock.Ui_Form, QWidget
# drawing_widget, drawing_base = create_ui('ui_drawingpad.ui'
mainwindow_widget, mainwindow_base = ui_mainwindow.Ui_MainWindow, QMainWindow
sync_widget, sync_base = ui_sync.Ui_Form, QWidget
dataentry_widget, dataentry_base = ui_dataentrywidget.Ui_Form, QWidget
report_widget, report_base = ui_reportwidget.Ui_Form, QWidget
featurefeature_dialog = ui_deletefeature.Ui_DeleteFeatureDialog
imageviewer_widget, imageviewer_base = ui_imageviewer.Ui_imageviewer, QWidget
actionpicker_widget, actionpicker_base = ui_actionpicker.Ui_ActionPickerDialog, QDialog
