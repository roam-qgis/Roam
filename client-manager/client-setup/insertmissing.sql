IF OBJECT_ID('tempdb..#Temp') IS NOT NULL DROP TABLE #Temp

Set Nocount On
SELECT scope
INTO #Temp
FROM [scopes] 
WHERE syncorder != 'Download'
Set Nocount OFF

Declare @scope varchar(max)
Declare @cols varchar(max), @query varchar(max)

While EXISTS(SELECT * From #Temp)
Begin
      Set Nocount On
    Select Top 1 @scope = scope From #Temp
      Set Nocount off
      
    SELECT  @cols = STUFF
    (
        ( 
            SELECT DISTINCT '], [' + name
            FROM sys.columns
            where object_id = (
                select top 1 object_id from sys.objects
                where name = @scope
            )
            and name not in ('JobID', 'UniqueID', 'AssetID')
            FOR XML PATH('')
        ), 1, 2, ''
    ) + ']'

    SET @query = 'INSERT INTO ' + @scope + '(' + @cols + ')
                    SELECT ' + @cols + ' FROM ' + @scope + '_old old
                          WHERE NOT EXISTS (SELECT * FROM ' + @scope + ' new
                                                             WHERE new.UniqueID = old.UniqueID)'
    exec(@query)
      print @query
      
      Set Nocount On
    Delete #Temp Where scope = @scope 
    Set Nocount Off
End




    
