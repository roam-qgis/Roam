declare @cols varchar(max), @query varchar(max)
SELECT  @cols = STUFF
    (
        ( 
            SELECT DISTINCT '], [' + name
            FROM sys.columns
            where object_id = (
                select top 1 object_id from sys.objects
                where name = 'WaterJobs'
            )
            and name not in ('JobID', 'UniqueID')
            FOR XML PATH('')
        ), 1, 2, ''
    ) + ']'
    
SET @query = 'INSERT INTO WaterJobs (' + @cols + ')
                    SELECT ' + @cols + ' FROM WaterJobs_old old
                          WHERE NOT EXISTS (SELECT * FROM WaterJobs j
                                                             WHERE j.UniqueID = old.UniqueID)'
exec(@query)