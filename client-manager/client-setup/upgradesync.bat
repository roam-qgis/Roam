@ECHO OFF

set TABLE_LIST=(WaterJobs, SewerJobs, ParkAssets)
set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CLIENT="Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"

sqlcmd -S SD0302 -d SpatialData -i backuptables.sql

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --reprovision --direction=UploadAndDownload
	)

syncer.exe --server=%SERVER% --client=%CLIENT% --reprovision
sqlcmd -S SD0302 -d SpatialData -i waterjobs.sql
syncer.exe --server=%SERVER% --client=%CLIENT% --reprovision