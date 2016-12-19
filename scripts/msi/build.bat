@ECHO OFF
SET PATH=%PATH%;"C:\Program Files (x86)\WiX Toolset v3.10\bin"
SET BASE=%~dp0..\..\dist
SET NAME=IntraMaps Roam
SET CANDELARGS=
SET ARGS=-ext WixUIExtension
SET LIGHTARGS=-sice:ICE60
SET VARS=-dQGISPATH="%BASE%" -dBINPATH="%BASE%"
SET WXSFILES=*.wxs build\*.wxs
SET WIXOBJ=build\*.wixobj

SET FLAGS=-template fragment -sreg -sfrag -ag -srd
heat dir "%BASE%" -cg bin -dr INSTALLLOCATION -out build\bin.wxs -var var.BINPATH %FLAGS%

ECHO %NAME%
ECHO %BASE%

candle %WXSFILES% %VARS% %ARGS% -out "%~dp0build\\"
light %WIXOBJ% -out "%~dp0..\..\release\%NAME%.msi" %VARS% %ARGS% %LIGHTARGS%
pause