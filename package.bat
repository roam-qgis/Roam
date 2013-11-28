@ECHO OFF

pushd %~dp0

ECHO Building Roam package

call setenv.bat
>package.log (
	python setup.py clean && python setup.py py2exe
)
popd

ECHO Package in dist\
ECHO Check package.log for build log

if defined DOUBLECLICKED pause
