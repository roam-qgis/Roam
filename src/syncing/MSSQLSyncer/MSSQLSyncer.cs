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

            int total_down = stats.DownloadChangesTotal + stats2.DownloadChangesTotal;
            int total_up = stats.UploadChangesApplied + stats2.UploadChangesTotal;

            Console.WriteLine(Resources.Program_Main_Changes_Downloaded__
                  + total_down
                  + Resources.Program_Main_
                  + total_up);
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
                    if (scope == "OneWay")
                    {
                        slaveProvider.ApplyChangeFailed += new EventHandler<Microsoft.Synchronization.Data.DbApplyChangeFailedEventArgs>(slaveProvider_ApplyChangeFailed);
                    }
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

        static void slaveProvider_ApplyChangeFailed(object sender, Microsoft.Synchronization.Data.DbApplyChangeFailedEventArgs e)
        {
            switch (e.Conflict.Type)
            {
                case Microsoft.Synchronization.Data.DbConflictType.ErrorsOccurred:
                    break;
                case Microsoft.Synchronization.Data.DbConflictType.LocalCleanedupDeleteRemoteUpdate:
                    break;
                case Microsoft.Synchronization.Data.DbConflictType.LocalDeleteRemoteDelete:
                    break;
                case Microsoft.Synchronization.Data.DbConflictType.LocalDeleteRemoteUpdate:
                    break;
                case Microsoft.Synchronization.Data.DbConflictType.LocalInsertRemoteInsert:
                    break;
                case Microsoft.Synchronization.Data.DbConflictType.LocalUpdateRemoteDelete:
                    break;
                case Microsoft.Synchronization.Data.DbConflictType.LocalUpdateRemoteUpdate:
                    e.Action = Microsoft.Synchronization.Data.ApplyAction.RetryWithForceWrite;
                    break;
                default:
                    break;
            }
        }
    }
}
