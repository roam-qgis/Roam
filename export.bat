@ECHO OFF

: Export QMap for client side install

CD %~dp0
call qmap-admin\build.bat "Melton Install"

: Over write the project file with the template one

SET PROJECT=export\IntraMaps Roam\projects\melton_firebreak
move /Y "%PROJECT%\fireinspect.qgs.tmpl" "%PROJECT%\fireinspect.qgs"
move /Y "%PROJECT%\Sync-All.bat.tmpl" "%PROJECT%\Sync-All.bat"
move /Y "%PROJECT%\Sync-Inspections.bat.tmpl" "%PROJECT%\Sync-Inspections.bat"

move /Y "%PROJECT%\_install" export\_install

: Write the update connection batch file

(
	ECHO @ECHO OFF
	ECHO python %%~dp0_install\update_connections.py
	ECHO pause
) > export\updateconnections.bat

: Write connections settings file used by update_connections.py

(
	echo # Replace with remote server and local server path
    echo RemoteServer: PATH TO SERVER
    echo LocalServer: PATH TO LOCAL SERVER
) > export\connectionstrings.txt
pause