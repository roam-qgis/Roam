@ECHO OFF

CD %~dp0

call setenv.bat

ECHO Building Roam package

>package.log 2>&1 (
	python build.py clean
	python build.py
	python setup.py py2exe
)

ECHO Package in dist\
ECHO Check package.log for build log and errors

if defined DOUBLECLICKED pause
