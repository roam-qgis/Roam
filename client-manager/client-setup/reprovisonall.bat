@ECHO OFF 

set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CLIENT="Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"

set TABLE_LIST=(AddressNumbers WaterMains WaterServices Cadastre RoadLabels LocalityBoundaries SewerNodes SewerPipes Towns WaterFittings WaterMeters)
set TWOWAYTABLE_LIST=(WaterJobs SewerJobs ParkAssets)

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i - Server
	provisioner.exe --server=%SERVER% --client=%SERVER% --table=%%i --reprovision
	ECHO Provisioning %%i - Client
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --reprovision
)

for %%i in %TWOWAYTABLE_LIST% DO (
	ECHO Provisioning %%i - Server
	provisioner.exe --server=%SERVER% --client=%SERVER% --table=%%i --reprovision --direction=UploadAndDownload
	ECHO Provisioning %%i - Client
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --reprovision --direction=UploadAndDownload
)