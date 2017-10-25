@ECHO OFF

ECHO Running Roam Config Manager from the src folder.
ECHO If you get errors make sure you run build.bat first to build the resources and UI files.

pushd %~dp0
CALL scripts\setenv.bat
python src\configmanager
