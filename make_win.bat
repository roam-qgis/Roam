@echo OFF
pyrcc4 -o resources.py resources.qrc
pyuic4 -o ui_datatimerpicker.py ui_datatimerpicker.ui
pyuic4 -o ui_listmodules.py ui_listmodules.ui
pause