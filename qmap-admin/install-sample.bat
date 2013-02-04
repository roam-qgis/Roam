@ECHO OFF

call src\setenv.bat

python src\build.py --target=Sample deploy
pause
