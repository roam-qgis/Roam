set SERVER="Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;"
set CLIENT="Data Source=localhost;Initial Catalog=SpatialData;Integrated Security=SSPI;"

sqlcmd -S SD0302 -d SpatialData -i backuptables.sql
provisioner.exe --server=%SERVER% --client=%CLIENT% --table="WaterJobs" --direction=UploadAndDownload --reprovision
syncer.exe --server=%SERVER% --client=%CLIENT% --table="WaterJobs" --reprovision
sqlcmd -S SD0302 -d SpatialData -i waterjobs.sql