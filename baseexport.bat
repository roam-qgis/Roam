call %~dp0qmap-admin\build.bat "%NAME%"
SET HOME=%~dp0export\%NAME%\IntraMaps Roam
git describe > "%HOME%\qmap\version.txt"
mkdir "%HOME%\docs"
copy /Y "%~dp0docs\IntraMaps Roam - User Guide.docx" "%HOME%\docs\IntraMaps Roam - User Guide.docx"
copy /Y "%~dp0installer\setenv.bat" "%HOME%\setenv.bat"