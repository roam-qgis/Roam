@echo off

REM MakeSFX
REM Makes the Self-extracting archive for patching IntraMaps
REM
setlocal

if %1=="" GOTO USAGE

set path="C:\Program Files\WINRAR";%path%
:RUN

cd %2
winrar a -r -sfx %1 -z"%~dp0sfx.cfg" -iimg"%~dp0logo.bmp" -iicon"%~dp0icon.ico"

GOTO Exit

:USAGE
ECHO Usage:
ECHO     makesfx ^<sfxname^> [working_folder]

:Exit