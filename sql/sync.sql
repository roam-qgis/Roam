Insert Into TestSlave1.dbo.TestTable
SELECT [UniqueID]
      ,[Data]
      ,[LastEditDate]
      ,[CreationDate]
      ,[MI_STYLE]
      ,[SP_GEOMETRY]
From TestMaster.dbo.TestTable T1
Where NOT EXISTS (Select * From TestSlave1.dbo.TestTable Where UniqueID = T1.UniqueID)





UPDATE [TestSlave1].[dbo].[TestTable]
   SET [Data] = T2.Data
      ,LastEditDate = T2.LastEditDate
      ,CreationDate = T2.CreationDate
      ,[MI_STYLE] = T2.MI_STYLE
      ,[SP_GEOMETRY] = T2.SP_GEOMETRY
FROM [TestSlave1].[dbo].[TestTable] T1
      JOIN [TestMaster].[dbo].[TestTable] T2
            ON T1.UniqueID = T2.UniqueID
            WHERE T1.LastEditDate < T2.LastEditDate





DELETE FROM [TestSlave1].[dbo].[TestTable]
      WHERE EXISTS (Select * From TestMaster.dbo.TestTable_Tombstone Where UniqueID = [TestSlave1].[dbo].[TestTable].UniqueID)





Insert Into TestMaster.dbo.TestTable
SELECT [UniqueID]
      ,[Data]
      ,[LastEditDate]
      ,[CreationDate]
      ,[MI_STYLE]
      ,[SP_GEOMETRY]
From TestSlave1.dbo.TestTable T1
Where NOT EXISTS (Select * From TestMaster.dbo.TestTable Where UniqueID = T1.UniqueID)



USE TestMaster
GO
DISABLE TRIGGER TestTable_UpdateTrigger ON TestTable
GO
UPDATE T1
   SET [Data] = T2.Data
      ,LastEditDate = T2.LastEditDate
      ,CreationDate = T2.CreationDate
      ,[MI_STYLE] = T2.MI_STYLE
      ,[SP_GEOMETRY] = T2.SP_GEOMETRY
FROM [TestMaster].[dbo].[TestTable] T1
      JOIN [TestSlave1].[dbo].[TestTable] T2
            ON T1.UniqueID = T2.UniqueID
            WHERE T1.LastEditDate < T2.LastEditDate
GO
ENABLE TRIGGER TestTable_UpdateTrigger ON TestTable
GO





DELETE FROM [TestMaster].[dbo].[TestTable]
      WHERE NOT EXISTS (Select * From TestSlave1.dbo.TestTable Where UniqueID = [TestMaster].[dbo].[TestTable].UniqueID)

