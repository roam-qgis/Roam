using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.Synchronization.Data;
using Microsoft.Synchronization.Data.SqlServer;
using Microsoft.Synchronization;
using Microsoft.SqlServer.Management.Smo;
using System.Data.SqlClient;
using System.Collections.Specialized;

public static class Provisioning
{
    public static void CreateScopesTable(SqlConnection conn)
    {
        string sql = @"IF NOT (EXISTS (SELECT * 
                                 FROM INFORMATION_SCHEMA.TABLES 
                                 WHERE TABLE_SCHEMA = 'dbo' 
                                 AND TABLE_NAME = 'scopes'))
                          BEGIN
                            CREATE TABLE [dbo].[scopes](
	                          [scope] [nvarchar](max) NULL,
	                          [syncorder] [nvarchar](max) NULL)
                          END";
        SqlCommand command = conn.CreateCommand();
        command.CommandText = sql;
        command.ExecuteNonQuery();
    }

    public static void AddScopeToScopesTable(SqlConnection conn, string scope,
                                             SyncDirectionOrder order)
    {
        CreateScopesTable(conn);

        string sql = @"DELETE FROM [scopes] WHERE scope = @scope;
                       INSERT INTO [scopes] ([scope] ,[syncorder])
                              VALUES (@scope, @order)";
        SqlCommand command = conn.CreateCommand();
        command.CommandText = sql;
        command.Parameters.AddWithValue("@scope", scope);
        command.Parameters.AddWithValue("@order", order.ToString());
        command.ExecuteNonQuery();
    }

    public static void ProvisionTable(SqlConnection server, SqlConnection client,
                                      string tableName)
    {
        ProvisionTable(server, client, tableName, false);
    }


    public static void ProvisionTable(SqlConnection server, SqlConnection client,
                                      string tableName, bool deprovisonScopeFirst)
    {
        bool clientMode = !client.ConnectionString.Equals(server.ConnectionString);

        DbSyncScopeDescription scopeDescription = new DbSyncScopeDescription(tableName);
        SqlSyncScopeProvisioning destinationConfig = new SqlSyncScopeProvisioning(client);

        if (deprovisonScopeFirst && destinationConfig.ScopeExists(tableName))
        {
            Deprovisioning.DropTable(client, tableName);
            Deprovisioning.DeprovisonScope(client, tableName);
        }

        // Get table info from server
        DbSyncTableDescription table = SqlSyncDescriptionBuilder.GetDescriptionForTable(tableName, server);
        DbSyncColumnDescription uniqueColumn = table.Columns.Where(f => f.Type == "uniqueidentifier").FirstOrDefault();
        DbSyncColumnDescription geometryColumn = table.Columns.Where(f => f.Type.EndsWith("geometry")).FirstOrDefault();
        DbSyncColumnDescription identityColumn = table.Columns.Where(f => f.AutoIncrementStepSpecified).FirstOrDefault();
        DbSyncColumnDescription joinColumn = table.PkColumns.FirstOrDefault();

        if (table.PkColumns.Count() != 1)
        {
            throw new SyncException(@"Table must have a single primary key column to be used with synchronisation.");
        }

        // Force uniqueidentifier as primary key to enable two way, if needed.
        if (uniqueColumn != null && 
            !uniqueColumn.IsPrimaryKey)
        {
            table.PkColumns.FirstOrDefault().IsPrimaryKey = false;
            uniqueColumn.IsPrimaryKey = true;
            joinColumn = uniqueColumn;
        }

        if (geometryColumn != null)
        {
            geometryColumn.ParameterName += "_was_geometry";
            geometryColumn.Type = "nvarchar";
            geometryColumn.Size = "max";
            geometryColumn.SizeSpecified = true;
        }

        // Remove identity columns from scope so that we don't get key conflicts.
        if (identityColumn != null && identityColumn != joinColumn)
        {
            table.Columns.Remove(identityColumn);
        }

        destinationConfig.SetCreateTableDefault(clientMode ? DbSyncCreationOption.Create 
                                                           : DbSyncCreationOption.Skip);
        
        // Add the table that we found on the server to the description.
        scopeDescription.Tables.Add(table);

        //It is important to call this after the tables have been added to the scope
        destinationConfig.PopulateFromScopeDescription(scopeDescription);

        // Drop the table from the client if we are in client mode
        // TODO We should sync the table first, but only if it is upload.
        if (clientMode)
        {
            if (client.State == System.Data.ConnectionState.Closed)
                client.Open();
            Deprovisioning.DropTable(client, tableName);
        }

        try
        {
            //provision the client
            destinationConfig.Apply();
        }
        catch (DbProvisioningException ex)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.Error.WriteLine(ex.Message);
            Console.ResetColor();
        }

        if (client.State == System.Data.ConnectionState.Closed)
            client.Open();
        SqlCommand command = client.CreateCommand();
        
        // Readd indentity column back onto client as primary key.
        if (clientMode && identityColumn != null && identityColumn != joinColumn)
        {
            string sql = @"ALTER TABLE [{1}] ADD {0} int IDENTITY(1,1) NOT NULL;
                           ALTER TABLE [{1}] DROP CONSTRAINT PK_{1};
                           ALTER TABLE [{1}] ADD CONSTRAINT PK_{1} PRIMARY KEY CLUSTERED ({0});";
            command.CommandText = String.Format(sql, identityColumn.QuotedName, tableName);
            command.ExecuteNonQuery();
        }

        // If we have a uniqueidentifier column and on client.  Add index and default value.
        if (uniqueColumn != null && clientMode && uniqueColumn == joinColumn)
        {
            string sql = @"ALTER TABLE [{1}] ADD UNIQUE ({0});
                           ALTER TABLE [{1}] ADD CONSTRAINT [DF_{1}_{2}]
                                 DEFAULT (newid()) FOR {0};";

            command.CommandText = String.Format(sql, uniqueColumn.QuotedName, 
                                                tableName,
                                                uniqueColumn.UnquotedName.Replace(' ', '_'));
            command.ExecuteNonQuery();
        }

        if (geometryColumn == null)
            return;
    
        // Everything after this point is for geometry based tables only.
        if (clientMode)
        {
            try
            {
                string sql = String.Format(@"ALTER TABLE [{0}] ALTER COLUMN [{1}] geometry;    
                                CREATE SPATIAL INDEX [ogr_{0}_sidx] ON [{0}]
                                (
                                    [{1}]
                                ) 
                                USING GEOMETRY_GRID WITH 
                                (
                                    BOUNDING_BOX =(300000, 6700000, 500000, 7000000), 
                                    GRIDS =(LEVEL_1 = MEDIUM,LEVEL_2 = MEDIUM,LEVEL_3 = MEDIUM,LEVEL_4 = MEDIUM), 
                                    CELLS_PER_OBJECT = 16, PAD_INDEX  = OFF, 
                                    SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, 
                                    ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON
                                ) ON [PRIMARY];",tableName, geometryColumn.UnquotedName);
                // Index
                command.CommandText = sql;
                //command.Parameters.AddWithValue("@table", tableName);
                //command.Parameters.AddWithValue("!geomcolumn", geometryColumn.QuotedName);
                command.ExecuteNonQuery();
            }
            catch (SqlException sqlException)
            {
                if (!sqlException.Message.Contains("already exists"))
                {
                    throw;
                }
            }
        }


        // Server and client. Drop trigger and create WKT transfer trigger.
        Deprovisioning.DropTableGeomTrigger(client, tableName);

        command.CommandText = string.Format(@"SELECT TOP 1 [srid]
                                              FROM [FieldData].[dbo].[geometry_columns] 
                                              WHERE [f_table_name] = '{0}'", 
                                            tableName);

        int srid = (command.ExecuteScalar() as int?).Value;

        command.CommandText = string.Format(@"CREATE TRIGGER [dbo].[{0}_GEOMSRID_trigger]
                                              ON [dbo].[{0}]
                                              AFTER INSERT, UPDATE
                                              AS UPDATE [dbo].[{0}] 
                                              SET [{1}].STSrid = {2}
                                              FROM [dbo].[{0}]
                                              JOIN inserted
                                              ON [dbo].[{0}].{3} = inserted.{3} AND inserted.[{1}] IS NOT NULL", tableName, geometryColumn.UnquotedName, srid, joinColumn.QuotedName);
        command.ExecuteNonQuery();

        // Alter selectedchanges stored procedure to convert geometry to WKT on fly.
        Server clientserver = new Server(client.DataSource);
        Database db = clientserver.Databases[client.Database];

        foreach (StoredProcedure sp in db.StoredProcedures.Cast<StoredProcedure>()
                                         .Where(sp => sp.Name.Equals(tableName + "_selectchanges", StringComparison.InvariantCultureIgnoreCase) 
                                             || sp.Name.Equals(tableName + "_selectrow", StringComparison.InvariantCultureIgnoreCase)))
        {
            sp.TextBody = sp.TextBody.Replace(geometryColumn.QuotedName, string.Format("{0}.STAsText() as {0}", geometryColumn.QuotedName));
            try
            {
                sp.Alter();   
            }
            catch (FailedOperationException ex)
            {
                if (ex.Operation != "Alter")
                {
                    throw;
                }
            }
        }
    }

    //public static StringCollection GetGeomTiggers(Database db, string tableName)
    //{
    //    Trigger inx = db.Tables[tableName].Triggers[string.Format("{0}_GEOMSRID_trigger",tableName)];
    //    Scripter scp = new Scripter(clientserver);
    //    return scp.Script(inx.Urn);
    //}
}
