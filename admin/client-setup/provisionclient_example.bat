@ECHO OFF 

set clientarg=%1

CALL setenv.bat

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe %CONN%  --scope=%%i
)

for %%i in %TWOWAYTABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe %CONN%  --scope=%%i --direction=UploadAndDownload
)