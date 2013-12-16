@ECHO OFF
IF NOT EXIST "%VS90COMNTOOLS%" GOTO NOVS

CALL "C:\OSGeo4W\bin\o4w_env.bat"

pushd %~dp0
curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -k | python
C:\OSGeo4W\apps\Python27\Scripts\easy_install.exe pip
pip install -r requirements.txt
popd && popd
GOTO END

:NOVS
ECHO You don't seem to have Visual Studio C++ 2008 installed.
ECHO We need that to build py2exe
GOTO END

:END
pause
