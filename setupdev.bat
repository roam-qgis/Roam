@ECHO OFF
IF NOT EXIST "%VS90COMNTOOLS%" GOTO NOVS

CALL "C:\OSGeo4W\bin\o4w_env.bat"

pushd %~dp0
mkdir temp
pushd temp
curl "http://waix.dl.sourceforge.net/project/py2exe/py2exe/0.6.9/py2exe-0.6.9.zip" > py2exe.zip
unzip -o py2exe.zip
pushd py2exe-0.6.9
python setup.py install
popd && popd
GOTO END

:NOVS
ECHO You don't seem to have Visual Studio C++ 2008 installed.
ECHO We need that to build py2exe
GOTO END

:END
pause
