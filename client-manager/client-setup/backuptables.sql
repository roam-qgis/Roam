-- Create a backup of all that can have data on the client.
-- We are making a backup so that we can merge any data is that is missing
-- from the server since we started doing a backup.

declare @sql varchar(max)
declare @tablenames varchar(max)

-- Drop old backup tables
select @tablenames = coalesce(@tablenames + ', ','') + scope + '_old' from [scopes]    
WHERE syncorder != 'Download' AND NOT OBJECT_ID(scope + '_old') IS NULL

set @sql = 'DROP TABLE ' + @tablenames

exec (@sql)

-- Backup tables
-- Get all the tables that are not download only.
IF OBJECT_ID('tempdb..#Temp') IS NOT NULL DROP TABLE #Temp

SELECT scope
INTO #Temp
FROM [scopes] 
WHERE syncorder != 'Download'

Declare @scope varchar(max)

SET ANSI_NULLS, QUOTED_IDENTIFIER ON

While EXISTS(SELECT * From #Temp)
Begin
    Select Top 1 @scope = scope From #Temp
	set @sql = 'SELECT * INTO ' + @scope + '_old' + ' FROM ' + @scope
	print @sql
	exec (@sql)
    Delete #Temp Where scope = @scope 
End