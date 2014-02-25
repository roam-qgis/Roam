@ECHO OFF

ECHO Running Roam from the src folder.
ECHO If you get errors make sure you run build.bat first to build the resources and UI files.

pushd %~dp0
CALL setenv.bat
python src\roam\__main__.py "%~dp0\src\projects"