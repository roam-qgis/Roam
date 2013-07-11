@ECHO OFF

: Export QMap for client side install

call %~dp0qmap-admin\build.bat "Melton Install"

: Over write the project file with the template one

SET HOME=%~dp0export\IntraMaps Roam
SET PROJECT=%HOME%\projects\melton_firebreak
move /Y "%PROJECT%\fireinspect.qgs.tmpl" "%PROJECT%\fireinspect.qgs"
move /Y "%PROJECT%\Sync-All.bat.tmpl" "%PROJECT%\Sync-All.bat"
move /Y "%PROJECT%\Sync-Inspections.bat.tmpl" "%PROJECT%\Sync-Inspections.bat"

move /Y "%PROJECT%\_install" "%HOME%\_install"

copy /Y "%~dp0installer\_createshortcut.bat" "%HOME%\_createshortcut.bat"
copy /Y "%~dp0installer\_updateconnections.bat" "%HOME%\_updateconnections.bat"