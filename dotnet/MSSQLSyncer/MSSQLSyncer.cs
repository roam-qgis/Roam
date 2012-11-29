namespace MSSQLSyncer
{
    using System;
    using System.Data.SqlClient;
    using Microsoft.Synchronization;
    using Microsoft.Synchronization.Data.SqlServer;
    using System.Collections.Generic;
    using Properties;
    using System.Linq;
    using Microsoft.Synchronization.Data;

    static class Program
    {
        /// <summary>The main entry point for the application.</summary>
        static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("Wrong number of args");
                printUsage();
                return;
            }

            string serverconn = "";
            string clientconn = "";
            string tablename = "";

            foreach (var arg in args)
            {
                Console.WriteLine(arg);
                var pairs = arg.Split(new char[] { '=' }, 2,
                                      StringSplitOptions.None);
                var name = pairs[0];
                string parm = pairs[1];
                switch (name)
                {
                    case "--server":
                        serverconn = parm;
                        break;
                    case "--client":
                        clientconn = parm;
                        break;
                    case "--table":
                        tablename = parm;
                        break;
                    default:
                        break;
                }
            }

            if (String.IsNullOrEmpty(serverconn))
            {
                Console.Error.WriteLine("We need a server connection string");
                printUsage();
                return;
            }

            // If there is no client then use local host.
            if (String.IsNullOrEmpty(clientconn))
            {
                clientconn = "Data Source=localhost;Initial Catalog=FieldData;Integrated Security=SSPI;";
            }

            
            Console.WriteLine("\n\r");

            Console.WriteLine("Running using these settings");
            Console.WriteLine("Server:" + serverconn);
            Console.WriteLine("Client:" + clientconn);
            Console.WriteLine("Table:" + (String.IsNullOrEmpty(tablename) ? "All tables" 
                                                                         : tablename ));

            string [] scopes = {"OneWay", "TwoWay"};

            int total_down = 0;
            int total_up = 0;
            foreach(string scope in scopes)
            {
                using (SqlConnection server = new SqlConnection(serverconn),
                                     client = new SqlConnection(clientconn))
                {
                   SyncOperationStatistics stats;
                   try
                   {
                       stats = syncscope(server, client, scope, SyncDirectionOrder.Download);
                       //stats = syncscope(server, client, "TwoWay", SyncDirectionOrder.DownloadAndUpload);
                   }
                   catch (DbSyncException ex)
                   {
                       Console.Error.WriteLine(ex.Message);
                       continue;
                   }
                   total_down += stats.DownloadChangesApplied;
                   total_up += stats.UploadChangesApplied;
                }
            }

            Console.WriteLine(Resources.Program_Main_Changes_Downloaded__
                  + total_down
                  + Resources.Program_Main_
                  + total_up);
#if DEBUG
            Console.Read();
#endif
        }

        /// <summary>
        /// Sync a single scope from the client to the server.
        /// </summary>
        /// <param name="server">Provider for the server.</param>
        /// <param name="client">Provider for the client.</param>
        /// <param name="tablename">The able name to sync.</param>
        static SyncOperationStatistics syncscope(SqlConnection server, SqlConnection client,
                              string scope, SyncDirectionOrder order)
        {
            using (SqlSyncProvider masterProvider = new SqlSyncProvider(scope, server),
                                    slaveProvider = new SqlSyncProvider(scope, client))
            {
                SyncOrchestrator orchestrator = new SyncOrchestrator
                {
                    LocalProvider = slaveProvider,
                    RemoteProvider = masterProvider,
                    Direction = order
                };

                orchestrator.SessionProgress += new EventHandler<SyncStagedProgressEventArgs>(orchestrator_SessionProgress);
                slaveProvider.ApplyChangeFailed += new EventHandler<DbApplyChangeFailedEventArgs>(slaveProvider_ApplyChangeFailed);

                SyncOperationStatistics stats = orchestrator.Synchronize();
                return stats;
            }
        }

        static void  orchestrator_SessionProgress(object sender, SyncStagedProgressEventArgs e)
        {
            DbSyncSessionProgressEventArgs sessionProgress = (DbSyncSessionProgressEventArgs)e;
            DbSyncScopeProgress progress = sessionProgress.GroupProgress;
            string message;
            switch (sessionProgress.DbSyncStage)
            {
                case DbSyncStage.SelectingChanges:
                    message = "Sync Stage: Selecting Changes";
                    Console.WriteLine(message);
                    foreach (DbSyncTableProgress tableProgress in progress.TablesProgress)
                    {
                        message = "Enumerated changes for table: " + tableProgress.TableName;
                        message += "[Inserts:" + tableProgress.Inserts.ToString() + "/Updates :" + tableProgress.Updates.ToString() + "/Deletes :" + tableProgress.Deletes.ToString() + "]";
                        Console.WriteLine(message);
                    }
                    break;
                case DbSyncStage.ApplyingChanges:
                    message = "Sync Stage: Applying Changes";
                    Console.WriteLine(message);
                    foreach (DbSyncTableProgress tableProgress in progress.TablesProgress)
                    {
                        message = "Applied changes for table: " + tableProgress.TableName;
                        message += "[Inserts:" + tableProgress.Inserts.ToString() + "/Updates :" + tableProgress.Updates.ToString() + "/Deletes :" + tableProgress.Deletes.ToString() + "]";
                        Console.WriteLine(message);
                    }
                    break;
                default:
                    break;
            }

            message = "Total Changes : " + progress.TotalChanges.ToString() + "  Inserts :" + progress.TotalInserts.ToString();
            message += "  Updates :" + progress.TotalUpdates.ToString() + "  Deletes :" + progress.TotalDeletes.ToString();
            Console.WriteLine(message);
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

        static void printUsage()
        {
            Console.WriteLine(@"provisioner --server={connectionstring} --table={tablename} [options]
[options]

--client={connectionstring} : The connection string to the client database. 
                              If blank will be set to server connection.
--direction=OneWay|TwoWay : The direction that the table will sync.
                            if blank will be set to OneWay.
--deprovision : Deprovision the table rather then provision. WARNING: Will drop
                the table on the client if client and server are different! Never
                drops server tables.");
        }
    }
}
