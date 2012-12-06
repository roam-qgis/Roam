using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.Synchronization.Data;
using Microsoft.Synchronization.Data.SqlServer;
using Microsoft.Synchronization;
using Microsoft.SqlServer.Management.Smo
using System.Data.SqlClient;
using System.Collections.Specialized;

class Provisioning
{
    public static void CreateScopesTable(SqlConnection conn)
    {
        throw new NotImplementedException();
    }

    public static void AddScopeToScopesTable(SqlConnection conn)
    {
        throw new NotImplementedException();
    }

    public static void ProvisionTable(SqlConnection server, SqlConnection client, 
                                      string tableName, int srid)
    {
        bool clientMode = !client.ConnectionString.Equals(server.ConnectionString);

        DbSyncScopeDescription scopeDescription = new DbSyncScopeDescription(tableName);
        SqlSyncScopeProvisioning destinationConfig = new SqlSyncScopeProvisioning(client);

        if (destinationConfig.ScopeExists(tableName))
        {
            throw new SyncConstraintConflictNotAllowedException(@"Scope already exists.  Please deprovision scope first.");
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

        destinationConfig.SetCreateTableDefault(clientMode ? DbSyncCreationOption.Create : DbSyncCreationOption.Skip);
        
        // Add the table that we found on the server to the d
        scopeDescription.Tables.Add(table);

        //It is important to call this after the tables have been added to the scope
        destinationConfig.PopulateFromScopeDescription(scopeDescription);

        //provision the server
        destinationConfig.Apply();

        client.Open();
        SqlCommand command = client.CreateCommand();
        
        // Readd indentity column back onto client as primary key.
        if (clientMode && identityColumn != null && identityColumn != joinColumn)
        {
            string sql = @"ALTER TABLE [@table] ADD @id int IDENTITY(1,1) NOT NULL;
                           ALTER TABLE [@table] DROP CONSTRAINT PK_@table;
                           ALTER TABLE [@table] ADD CONSTRAINT PK_@table PRIMARY KEY CLUSTERED (@id;";
            command.CommandText = sql;
            command.Parameters.Add("@table", tableName);
            command.Parameters.Add("@id", identityColumn.QuotedName);
            command.ExecuteNonQuery();
        }

        // If we have a uniqueidentifier column and on client.  Add index and default value.
        if (uniqueColumn != null && clientMode && uniqueColumn == joinColumn)
        {  
            string sql = @"ALTER TABLE [@table] ADD UNIQUE (@uniquecolumn);
                           ALTER TABLE [@table] ADD CONSTRAINT [DF_@table_@uniquecolumnescape]
                                 DEFAULT (newid()) FOR uniquecolumn;";

            command.CommandText = sql;
            command.Parameters.Add("@table", tableName);
            command.Parameters.Add("@uniquecolumn", uniqueColumn.QuotedName);
            command.Parameters.Add("@uniquecolumnescape", uniqueColumn.UnquotedName.Replace(' ', '_'));
            command.ExecuteNonQuery();
        }

        if (geometryColumn == null)
            return;
    
        // Everything after this point is for geometry based tables only.
        if (clientMode)
        {
            try
            {
                string sql  = @"ALTER TABLE [@table] ALTER COLUMN @geomcolumn geometry;
                                CREATE SPATIAL INDEX [ogr_@table_sidx] ON [@table]
                                (
                                    @geomcolumn
                                ) 
                                USING GEOMETRY_GRID WITH 
                                (
                                    BOUNDING_BOX =(300000, 6700000, 500000, 7000000), 
                                    GRIDS =(LEVEL_1 = MEDIUM,LEVEL_2 = MEDIUM,LEVEL_3 = MEDIUM,LEVEL_4 = MEDIUM), 
                                    CELLS_PER_OBJECT = 16, PAD_INDEX  = OFF, 
                                    SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, 
                                    ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON
                                ) ON [PRIMARY];";
                // Index
                command.CommandText = sql;
                command.Parameters.Add("@table", tableName);
                command.Parameters.Add("@geomcolumn", geometryColumn.QuotedName);
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
            sp.Alter();
        }
    }

    //public static StringCollection GetGeomTiggers(Database db, string tableName)
    //{
    //    Trigger inx = db.Tables[tableName].Triggers[string.Format("{0}_GEOMSRID_trigger",tableName)];
    //    Scripter scp = new Scripter(clientserver);
    //    return scp.Script(inx.Urn);
    //}
}
