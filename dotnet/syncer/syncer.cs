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
        static bool porcelain = false;

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
            string scopetosync = "";

            foreach (var arg in args)
            {
                var pairs = arg.Split(new char[] { '=' }, 2,
                                      StringSplitOptions.None);
                var name = pairs[0];
                string parm = "";
                if (pairs.Length == 2)
                    parm = pairs[1];

                switch (name)
                {
                    case "--server":
                        serverconn = parm;
                        break;
                    case "--client":
                        clientconn = parm;
                        break;
                    case "--scope":
                        scopetosync = parm;
                        break;
                    case "--porcelain":
                        porcelain = true;
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


            if (!porcelain)
            {
                Console.WriteLine("\n\r");

                Console.WriteLine("Running using these settings");
                Console.WriteLine("Server:" + serverconn);
                Console.WriteLine("Client:" + clientconn);
                Console.WriteLine("Table:" + (String.IsNullOrEmpty(scopetosync) ? "All scopes"
                                                                             : scopetosync));
            }

            List<syncing.Scope> scopes;

            if (!String.IsNullOrEmpty(scopetosync))
            {
                scopes = syncing.getScopes(clientconn, scopetosync);
            }
            else
            {
                scopes = syncing.getScopes(clientconn);
            }

            int total_down = 0;
            int total_up = 0;
            foreach (syncing.Scope scope in scopes)
            {
                using (SqlConnection server = new SqlConnection(serverconn),
                                     client = new SqlConnection(clientconn))
                {
                   SyncOperationStatistics stats;
                   try
                   {
                       stats = syncing.syncscope(server, client, 
                                                 scope.name, scope.order,
                                                 applyingChanges);
                   }
                   catch (DbSyncException ex)
                   {
                       Console.Error.WriteLine(ex.Message);
                       continue;
                   }
                   catch (SqlException ex)
                   {
                        Console.WriteLine("Error:" + ex.Message);
                        continue;
                   }
                   total_down += stats.DownloadChangesApplied;
                   total_up += stats.UploadChangesApplied;
                }
            }

            if (porcelain)
            {
                string message;
                message = "td:" + total_down +
                           "|tu:" + total_up;
                Console.WriteLine(message);
            }
            else
            {
                Console.WriteLine(Resources.Program_Main_Changes_Downloaded__
                                  + total_down
                                  + Resources.Program_Main_
                                  + total_up);
            }
        }

        /// <summary>
        /// Reports the progress on the changes being applied.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        static void applyingChanges(object sender, DbApplyingChangesEventArgs e)
        {
            string message;
            foreach (DbSyncTableProgress tableProgress in e.Context.ScopeProgress.TablesProgress)
            {
                if (porcelain)
                {
                    message = "t:" + tableProgress.TableName;
                    message += "|i:" + tableProgress.Inserts.ToString() +
                               "|u:" + tableProgress.Updates.ToString() +
                               "|d:" + tableProgress.Deletes.ToString();
                }
                else
                {
                    message = "Applied changes for table: " + tableProgress.TableName;
                    message += " [ Inserts:" + tableProgress.Inserts.ToString() +
                               " | Updates :" + tableProgress.Updates.ToString() +
                               " | Deletes :" + tableProgress.Deletes.ToString() + " ]";
                }
                Console.WriteLine(message);
            }
        }

        static void printUsage()
        {
            Console.WriteLine(@"syncer --server={connectionstring} --client={connectionstring} --scope={scope}

--client={connectionstring} : The connection string to the client database. 

--scope : The scope to sync from the database.  If blank all scopes will be synced.");
        }
    }
}
