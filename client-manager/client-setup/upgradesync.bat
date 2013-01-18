@ECHO OFF

REM Update the client to use the new table per scope syncing style.
REM This allows us to update clients one by one by not loose data between the sync.
REM Only handles new records not changed data on client.


set TABLE_LIST=(WaterJobs, ParkAssets)
set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CLIENT="Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"

sqlcmd -S SD0302 -d SpatialData -i backuptables.sql

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --reprovision --direction=UploadAndDownload
	)

syncer.exe --server=%SERVER% --client=%CLIENT%
sqlcmd -S SD0302 -d SpatialData -i insertmissing.sql
syncer.exe --server=%SERVER% --client=%CLIENT%