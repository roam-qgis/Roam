@ECHO OFF

set clientarg=%1

REM Update the client to use the new table per scope syncing style.
REM This allows us to update clients one by one by not loose data between the sync.
REM Only handles new records not changed data on client.

CALL setenv.bat

set TABLE_LIST=(AddressNumbers WaterMains WaterServices Cadastre RoadLabels LocalityBoundaries SewerNodes SewerPipes Towns WaterFittings WaterMeters)
set TWOWAYTABLE_LIST=(WaterJobs SewerJobs ParkAssets)

REM Backup the twoway tables and update them first.

sqlcmd %sqlcmdargs% -i backuptables.sql

provisioner.exe %CONN% --scope=OneWay --deprovision --dontdroptables
provisioner.exe %CONN% --scope=TwoWay --deprovision --dontdroptables

for %%i in %TWOWAYTABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe %CONN% --scope=%%i --reprovision --direction=UploadAndDownload
	ECHO.
	)

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe %CONN% --scope=%%i --reprovision
	ECHO.
	)

syncer.exe %CONN%
sqlcmd %sqlcmdargs% -i insertmissing.sql
syncer.exe %CONN%