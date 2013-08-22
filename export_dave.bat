@ECHO OFF

: Export QMap for client side install

SET NAME=Dave Demo

call baseexport.bat

SET PROJECT=%HOME%\projects\foothpath_inspection
move /Y "%PROJECT%\footpaths.qgs.tmpl" "%PROJECT%\footpaths.qgs"
move /Y "%PROJECT%\Sync-Inspections.bat.tmpl" "%PROJECT%\Sync-Inspections.bat"

SET PROJECT=%HOME%\projects\pool_sample
move /Y "%PROJECT%\Pool (Sample).qgs.tmpl" "%PROJECT%\Pool (Sample).qgs"
move /Y "%PROJECT%\Sync-Inspections.bat.tmpl" "%PROJECT%\Sync-Inspections.bat"

SET PROJECT=%HOME%\projects\septic_tank_audit
move /Y "%PROJECT%\Septic Tank Audit.qgs.tmpl" "%PROJECT%\Septic Tank Audit.qgs"
move /Y "%PROJECT%\Sync-Inspections.bat.tmpl" "%PROJECT%\Sync-Inspections.bat"

pause