namespace MSSQLSyncer
{
    using System;
    using System.Data.SqlClient;
    using Microsoft.Synchronization;
    using Microsoft.Synchronization.Data.SqlServer;
    using Properties;

    static class Program
    {
        /// <summary>The main entry point for the application.</summary>
        static void Main()
        {
            SyncOperationStatistics stats = sync("OneWay", SyncDirectionOrder.Download);
            SyncOperationStatistics stats2 = sync("TwoWay", SyncDirectionOrder.DownloadAndUpload);
            if (stats == null || stats2 == null)
                return;

            Console.WriteLine(Resources.Program_Main_Changes_Downloaded__
                  + stats.DownloadChangesTotal + stats2.DownloadChangesTotal
                  + Resources.Program_Main_
                  + stats.UploadChangesApplied + stats2.UploadChangesTotal);
        }

        static SyncOperationStatistics sync(string scope, SyncDirectionOrder order)
        {
            using (SqlSyncProvider masterProvider = new SqlSyncProvider { ScopeName = scope },
                     slaveProvider = new SqlSyncProvider { ScopeName = scope })
            {
                using (SqlConnection master = new SqlConnection(Settings.Default.ServerConnectionString),
                                     slave = new SqlConnection(Settings.Default.ClientConnectionString))
                {
                    masterProvider.Connection = master;
                    slaveProvider.Connection = slave;

                    SyncOrchestrator orchestrator = new SyncOrchestrator
                    {
                        LocalProvider = slaveProvider,
                        RemoteProvider = masterProvider,
                        Direction = order
                    };

                    try
                    {
                        SyncOperationStatistics stats = orchestrator.Synchronize();
                        return stats;
                    }
                    catch (Exception ex)
                    {
                        Console.Error.WriteLine(ex.Message);
                        return null;
                    }
                }
            }
        }
    }
}
