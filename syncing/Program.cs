namespace SyncProofConcept
{
    using System;
    using Microsoft.Synchronization;
    using Microsoft.Synchronization.Data.SqlServer;
    using System.Windows.Forms;
    using System.Data.SqlClient;
    using Properties;

    static class Program
    {
        public const string Scope = "SpatialScope";

        /// <summary>The main entry point for the application.</summary>
        static void Main()
        {
            using (SqlSyncProvider masterProvider = new SqlSyncProvider { ScopeName = Scope }, slaveProvider = new SqlSyncProvider { ScopeName = Scope })
            {
                using (SqlConnection master = new SqlConnection(Settings.Default.ServerConnectionString), slave = new SqlConnection(Settings.Default.ClientConnectionString))
                {
                    masterProvider.Connection = master;
                    slaveProvider.Connection = slave;
                }

                SyncOrchestrator orchestrator = new SyncOrchestrator
                {
                    LocalProvider = slaveProvider,
                    RemoteProvider = masterProvider,
                    Direction = SyncDirectionOrder.UploadAndDownload
                };

                try
                {
                    SyncOperationStatistics stats = orchestrator.Synchronize();
                    Console.WriteLine(Resources.Program_Main_Changes_Downloaded__ + stats.DownloadChangesTotal + Resources.Program_Main_ + stats.UploadChangesApplied);
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine(ex.Message);
                }
            }
        }
    }
}
