@ECHO OFF 

set TABLE_LIST=(SewerJobs WaterJobs ParkAssets AddressNumbers WaterMains WaterServices Cadastre RoadLabels LocalityBoundaries SewerNodes SewerPipes Towns WaterFittings WaterMeters)
set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe --server=%SERVER% --client=%SERVER% --table=%%i --srid=28356)
