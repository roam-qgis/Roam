@ECHO OFF

set SERVER="Data Source=SD0302;Initial Catalog=SpatialData;Integrated Security=SSPI;"
set CLIENT="Data Source=%clientarg%;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CONN=--server=%SERVER% --client=%CLIENT%
set sqlcmdargs=-S %clientarg% -d FieldData 

set TABLE_LIST=(AddressNumbers WaterMains WaterServices Cadastre RoadLabels LocalityBoundaries SewerNodes SewerPipes Towns WaterFittings WaterMeters)
set TWOWAYTABLE_LIST=(WaterJobs SewerJobs ParkAssets)