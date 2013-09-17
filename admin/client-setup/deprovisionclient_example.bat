@ECHO OFF 

set clientarg=%1

CALL setenv.bat

for %%i in %TABLE_LIST% DO (
	ECHO Deprovisioning %%i
	provisioner.exe %CONN% --scope=%%i --deprovision --dontdroptables
)

for %%i in %TWOWAYTABLE_LIST% DO (
	ECHO Deprovisioning %%i
	provisioner.exe %CONN% --scope=%%i --deprovision --dontdroptables
)