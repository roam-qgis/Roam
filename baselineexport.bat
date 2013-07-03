cd %~dp0
SET SPHINXOPTS=-Q
ECHO Building docs
call docs\makehtml.bat
cd %~dp0
copy docs\build "..\Intramaps Roam Admin\docs\build\"
ECHO Exporting source...
git checkout-index -f -a --prefix="../Intramaps Roam Admin/"
