@rem MakeSFX
@rem Makes the Self-extracting archive for patching IntraMaps
@rem
@setlocal
@echo off


if %1=="" GOTO Usage


set path="C:\Program Files\WINRAR";%path%
:run
cd %2
winrar a -r -sfx %1 -z"%~dp0sfx.cfg" -iimg"%~dp0logo.bmp" -iicon"%~dp0icon.ico"

GOTO Exit

:Usage
echo Usage:
echo     makesfx ^<sfxname^> [working_folder]
echo. 

:Exit