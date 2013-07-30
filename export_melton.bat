@ECHO OFF

: Export QMap for client side install

SET NAME=Melton Install

call baseexport.bat

: Over write the project file with the template one

SET PROJECT=%HOME%\projects\melton_firebreak
move /Y "%PROJECT%\fireinspect.qgs.tmpl" "%PROJECT%\fireinspect.qgs"
move /Y "%PROJECT%\Sync-All.bat.tmpl" "%PROJECT%\Sync-All.bat"
move /Y "%PROJECT%\Sync-Inspections.bat.tmpl" "%PROJECT%\Sync-Inspections.bat"
move /Y "%PROJECT%\_docs\*" "%HOME%\docs\"


