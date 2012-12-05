
namespace SqlSyncProvisioner
{
    using System;
    using System.Linq;
    using System.Data.SqlClient;
    using Microsoft.SqlServer.Management.Smo;
    using Microsoft.Synchronization;
    using Microsoft.Synchronization.Data;
    using Microsoft.Synchronization.Data.SqlServer;

    public static class TableProvisioning
    {
        public static void ProvisionTable(SqlConnection master, SqlConnection destination, string tableName, int srid, bool oneWayOnly)
        {
            bool isSlave = false;
            if (!destination.ConnectionString.Equals(master.ConnectionString))
            {
                isSlave = true;
            }

            DbSyncScopeDescription scopeDescription = new DbSyncScopeDescription(tableName);
            SqlSyncScopeProvisioning destinationConfig = new SqlSyncScopeProvisioning(destination);
            if (destinationConfig.ScopeExists(tableName))
            {
                throw new SyncConstraintConflictNotAllowedException(@"Scope already exists.  Please deprovision scope first.");
            }

            DbSyncTableDescription table = SqlSyncDescriptionBuilder.GetDescriptionForTable(tableName, master);
            DbSyncColumnDescription uniqueColumn = table.Columns.Where(f => f.Type == "uniqueidentifier").FirstOrDefault();
            DbSyncColumnDescription geometryColumn = table.Columns.Where(f => f.Type.EndsWith("geometry")).FirstOrDefault();
            DbSyncColumnDescription identityColumn = table.Columns.Where(f => f.AutoIncrementStepSpecified).FirstOrDefault();
            DbSyncColumnDescription joinColumn = table.PkColumns.FirstOrDefault();

            if (table.PkColumns.Count() != 1)
            {
                throw new SyncException(@"Table must have a single primary key column to be used with synchronisation.");
            }

            if (uniqueColumn != null && !uniqueColumn.IsPrimaryKey && !oneWayOnly)
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

            if (identityColumn != null && identityColumn != joinColumn)
            {
                table.Columns.Remove(identityColumn);
            }

            destinationConfig.SetCreateTableDefault(isSlave ? DbSyncCreationOption.Create : DbSyncCreationOption.Skip);
            scopeDescription.Tables.Add(table);

            //It is important to call this after the tables have been added to the scope
            destinationConfig.PopulateFromScopeDescription(scopeDescription);

            //provision the server
            destinationConfig.Apply();

            destination.Open();
            SqlCommand command = destination.CreateCommand();
            if (isSlave && identityColumn != null && identityColumn != joinColumn)
            {
                command.CommandText = string.Format("ALTER TABLE [{0}] ADD {1} int IDENTITY(1,1) NOT NULL", tableName, identityColumn.QuotedName);
                command.ExecuteNonQuery();
                command.CommandText = string.Format("ALTER TABLE [{0}] DROP CONSTRAINT PK_{0}", tableName);
                command.ExecuteNonQuery();
                command.CommandText = string.Format("ALTER TABLE [{0}] ADD CONSTRAINT PK_{0} PRIMARY KEY CLUSTERED ({1})", tableName, identityColumn.QuotedName);
                command.ExecuteNonQuery();
            }

            if (uniqueColumn != null && isSlave && uniqueColumn == joinColumn)
            {
                command.CommandText = string.Format("ALTER TABLE [{0}] ADD UNIQUE ({1})", tableName, uniqueColumn.QuotedName);
                command.ExecuteNonQuery();
                command.CommandText = string.Format("ALTER TABLE [{0}] ADD CONSTRAINT [DF_{0}_{2}]  DEFAULT (newid()) FOR {1}", tableName, uniqueColumn.QuotedName, uniqueColumn.UnquotedName.Replace(' ', '_'));
                command.ExecuteNonQuery();
            }

            if (geometryColumn == null)
            {
                return;
            }

            if (isSlave)
            {
                command.CommandText = string.Format("ALTER TABLE [{0}] ALTER COLUMN {1} geometry", tableName, geometryColumn.QuotedName);
                command.ExecuteNonQuery();
                try
                {
                    command.CommandText = string.Format("CREATE SPATIAL INDEX [ogr_{2}_sidx] ON [{0}]({1}) USING  GEOMETRY_GRID WITH (BOUNDING_BOX =(300000, 6700000, 500000, 7000000), GRIDS =(LEVEL_1 = MEDIUM,LEVEL_2 = MEDIUM,LEVEL_3 = MEDIUM,LEVEL_4 = MEDIUM), CELLS_PER_OBJECT = 16, PAD_INDEX  = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]", tableName, geometryColumn.QuotedName, geometryColumn.UnquotedName);
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

            command.CommandText = string.Format("IF  EXISTS (SELECT * FROM sys.triggers WHERE object_id = OBJECT_ID(N'[dbo].[{0}_GEOMSRID_trigger]')) DROP TRIGGER [dbo].[{0}_GEOMSRID_trigger]", tableName);
            command.ExecuteNonQuery();
            command.CommandText = string.Format("CREATE TRIGGER [dbo].[{0}_GEOMSRID_trigger]\nON [dbo].[{0}]\nAFTER INSERT, UPDATE\nAS UPDATE [dbo].[{0}] SET [{1}].STSrid = {2}\nFROM [dbo].[{0}]\nJOIN inserted\nON [dbo].[{0}].{3} = inserted.{3} AND inserted.[{1}] IS NOT NULL", tableName, geometryColumn.UnquotedName, srid, joinColumn.QuotedName);
            command.ExecuteNonQuery();
            Server server = new Server(destination.DataSource);
            Database db = server.Databases[destination.Database];
            foreach (StoredProcedure sp in db.StoredProcedures.Cast<StoredProcedure>().Where(sp => sp.Name.Equals(tableName + "_selectchanges", StringComparison.InvariantCultureIgnoreCase) || sp.Name.Equals(tableName + "_selectrow", StringComparison.InvariantCultureIgnoreCase)))
            {
                sp.TextBody = sp.TextBody.Replace(geometryColumn.QuotedName, string.Format("{0}.STAsText() as {0}", geometryColumn.QuotedName));
                sp.Alter();
            }
        }
    }
}
