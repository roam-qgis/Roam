@ECHO OFF 

REM This is an exmaple of a provision script that can be used to prepare a set of tables for syncing
REM We list each table that should be synced in the TABLE_LIST variable and loop each one to provision it
REM If a layer is already provisioned an error will be thrown.  To handle this you need to use the --deprovision
REM flag and then call provision.exe again.

set TABLE_LIST=(SewerJobs WaterJobs ParkAssets AddressNumbers WaterMains WaterServices Cadastre RoadLabels LocalityBoundaries SewerNodes SewerPipes Towns WaterFittings WaterMeters)
set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"

for %%i in %TABLE_LIST% DO (
	ECHO Provisioning %%i
	provisioner.exe --server=%SERVER% --client=%SERVER% --table=%%i --srid=28356)
