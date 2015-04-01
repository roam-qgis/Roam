@echo off

REM MakeSFX
REM Makes the Self-extracting archive for patching IntraMaps
REM
setlocal enabledelayedexpansion

if %1=="" GOTO USAGE

set path="C:\Program Files\WINRAR";%path%

IF "%3" == "-s" (
    set NAME=%~dp0sfx-silent.cfg
) ELSE (
    set NAME=%~dp0sfx.cfg
)

ECHO !NAME!

:RUN

cd %2
winrar a -r -sfx %1 -z"!NAME!" -iimg"%~dp0logo.bmp" -iicon"%~dp0icon.ico"

GOTO Exit

:USAGE
ECHO Usage:
ECHO     makesfx ^<sfxname^> [working_folder]

:Exit