@rem MakeSFX
@rem Makes the Self-extracting archive for patching IntraMaps
@rem
@setlocal
@echo off


if "%1"=="" GOTO Usage


set path="C:\Program Files\WINRAR";%path%
@rem if "%2"=="" GOTO run
@rem cd "%2"
:run
winrar a -r -sfx %1 -zC:\Projects\vcsharp2008\IntraMaps75\sfx.cfg ^
 -iimgC:\Projects\vcsharp2008\IntraMaps75\DMS.bmp^
 -iiconC:\Projects\vcsharp2008\IntraMaps75\IntraMaps.ico^
 -ibck @C:\Projects\vcsharp2008\IntraMaps75\file.txt

GOTO Exit


:Usage
echo Usage:
echo     makesfx ^<sfxname^> [working_folder]
echo. 


:Exit