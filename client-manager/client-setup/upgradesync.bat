@ECHO OFF

REM Update the client to use the new table per scope syncing style.
REM This allows us to update clients one by one by not loose data between the sync.
REM Only handles new records not changed data on client.

set clientarg=%1
set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CLIENT="Data Source=%clientarg%;Initial Catalog=SpatialData;Integrated Security=SSPI;"
set TABLE_LIST=(AddressNumbers WaterMains WaterServices Cadastre RoadLabels LocalityBoundaries SewerNodes SewerPipes Towns WaterFittings WaterMeters)
set TWOWAYTABLE_LIST=(WaterJobs SewerJobs ParkAssets)

REM Backup the twoway tables and update them first.

sqlcmd -S SD0302 -d SpatialData -i backuptables.sql

for %%i in %TWOWAYTABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --reprovision --direction=UploadAndDownload
	ECHO.
	)

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --reprovision
	ECHO.
	)

syncer.exe --server=%SERVER% --client=%CLIENT%
sqlcmd -S %clientarg% -d SpatialData -i insertmissing.sql
syncer.exe --server=%SERVER% --client=%CLIENT%