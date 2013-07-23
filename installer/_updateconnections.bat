@ECHO OFF
: Set to the address of the local and remote server
Set REMOTESERVER=
Set LOCALSERVER=

CALL setenv.bat

TITLE IntraMaps Roam Installer
python "%~dp0_install\postinstall.py" --remote_server %REMOTESERVER% --local_server %LOCALSERVER%
pause
