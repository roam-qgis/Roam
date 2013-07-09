@ECHO OFF
CD %~dp0
call qmap-admin\build.bat "Melton Install"
xcopy /S /Y projects\melton_firebreak\_install export\_install\
pause