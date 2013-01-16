IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[WaterJobs_old]') AND type in (N'U'))
DROP TABLE [dbo].[WaterJobs_old]
GO
SELECT * INTO WaterJobs_old FROM WaterJobs