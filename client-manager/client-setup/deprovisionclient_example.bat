@ECHO OFF 

set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CLIENT="Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"

set TABLE_LIST=(AddressNumbers WaterMains WaterServices Cadastre RoadLabels LocalityBoundaries SewerNodes SewerPipes Towns WaterFittings WaterMeters)
set TWOWAYTABLE_LIST=(WaterJobs SewerJobs ParkAssets)

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	REM Uncomment then following line if you need to reprovision the tables
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --srid=28356 --deprovision
	REM provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --srid=28356
)

for %%i in %TWOWAYTABLE_LIST% DO (
	ECHO Provisioning %%i
	REM Uncomment then following line if you need to reprovision the tables
	provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --srid=28356 --deprovision
	REM provisioner.exe --server=%SERVER% --client=%CLIENT% --table=%%i --srid=28356 --direction=UploadAndDownload
)