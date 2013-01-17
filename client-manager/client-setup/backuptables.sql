declare @sql varchar(max)
declare @tablenames varchar(max)

-- Drop old backup tables
select @tablenames = coalesce(@tablenames + ', ','') + scope + '_old' from [scopes]    
WHERE syncorder != 'Download' AND NOT OBJECT_ID(scope + '_old') IS NULL

set @sql = 'DROP TABLE ' + @tablenames

exec (@sql)

-- Backup tables
-- Get all the tables that are not download only.
-- IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[#Temp]') AND type in (N'U'))
DROP TABLE #Temp

SELECT scope
INTO #Temp
FROM [scopes] 
WHERE syncorder != 'Download'

Declare @scope varchar(max)

While EXISTS(SELECT * From #Temp)
Begin
    Select Top 1 @scope = scope From #Temp
	set @sql = 'SELECT * INTO ' + @scope + '_old' + ' FROM ' + @scope
	print @sql
	exec (@sql)
    Delete #Temp Where scope = @scope 
End