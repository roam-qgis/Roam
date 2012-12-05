using System;
using System.Data.SqlClient;
using Microsoft.Synchronization;
using Microsoft.Synchronization.Data.SqlServer;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Synchronization.Data;

public static class syncing
{
    public class Scope
    {
        public string name;
        public SyncDirectionOrder order;
    }

    /// <summary>
    /// Return all the scopes defined in the database.
    /// </summary>
    /// <param name="clientconn"></param>
    /// <returns></returns>
    public static List<Scope> getScopes(string clientconn)
    {
        return getScopes(clientconn, null);
    }

    /// <summary>
    /// Returns the scopes and their sync order that are defined in the database.
    /// </summary>
    /// <param name="clientconn">The connection string to the client</param>
    /// <param name="scope">The name of the scope to sync. If blank return
    /// all scopes.</param>
    /// <returns>A list of <see cref="Scope"/> that contains a name and order</returns>
    public static List<Scope> getScopes(string clientconn, string scope)
    {
        List<Scope> scopes = new List<Scope>();
        using (SqlConnection client = new SqlConnection(clientconn))
        {
            client.Open();
            string command = "SELECT scope, syncorder FROM scopes";
            SqlCommand query = new SqlCommand(command, client);
            if (!String.IsNullOrEmpty(scope))
            {
                query.CommandText += " WHERE scope = @scope";
                SqlParameter param = new SqlParameter();
                param.ParameterName = "@scope";
                param.Value = scope;
                query.Parameters.Add(param);
            }

            // We should handle if the table scopes doesn't exist and maybe
            // grab all the scopes from the database and just sync one way.

            SqlDataReader reader = query.ExecuteReader();
            while (reader.Read())
            {
                string name = reader["scope"].ToString();
                string order = reader["syncorder"].ToString();
                SyncDirectionOrder syncorder = StringToEnum<SyncDirectionOrder>(order);
                scopes.Add(new Scope() { name = name, order = syncorder });
            }
            client.Close();
        }
        return scopes;
    }

    /// <summary>
    /// Sync a single scope from the client to the server.
    /// </summary>
    /// <param name="server">Provider for the server.</param>
    /// <param name="client">Provider for the client.</param>
    /// <param name="tablename">The able name to sync.</param>
    public static SyncOperationStatistics syncscope(SqlConnection server, SqlConnection client,
                          string scope, SyncDirectionOrder order, 
                          Action<object, DbApplyingChangesEventArgs> callback)
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

            slaveProvider.ApplyingChanges += new EventHandler<DbApplyingChangesEventArgs>(callback);
            masterProvider.ApplyingChanges += new EventHandler<DbApplyingChangesEventArgs>(callback);
            slaveProvider.ApplyChangeFailed += slaveProvider_ApplyChangeFailed;
            return orchestrator.Synchronize();
        }
    }

    public static T StringToEnum<T>(string name)
    {
        return (T)Enum.Parse(typeof(T), name);
    }

    /// <summary>
    /// Handles errors that happen during syncing down to the client.
    /// </summary>
    /// <param name="sender"></param>
    /// <param name="e"></param>
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
                // If there are server edits and local edits then the server always wins.
                e.Action = ApplyAction.RetryWithForceWrite;
                break;
            default:
                break;
        }
    }
}