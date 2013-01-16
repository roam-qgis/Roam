@echo off

set TABLE_LIST=(WaterJobs)
set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CLIENT="Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --reprovision --direction=UploadAndDownload
	)
