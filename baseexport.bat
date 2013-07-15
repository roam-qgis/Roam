call %~dp0qmap-admin\build.bat "%NAME%"
SET HOME=%~dp0export\%NAME%\IntraMaps Roam
copy /Y "%~dp0installer\_updateconnections.bat" "%HOME%\_updateconnections.bat"
xcopy /Y "%~dp0installer\_install" "%HOME%\_install\"