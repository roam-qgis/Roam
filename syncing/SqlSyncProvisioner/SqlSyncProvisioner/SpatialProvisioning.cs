
namespace SqlSyncProvisioner
{
    using System;
    using System.Collections.Generic;
    using System.Data.SqlClient;
    using System.Linq;
    using Microsoft.Synchronization.Data;
    using Microsoft.Synchronization.Data.SqlServer;
    using Microsoft.SqlServer.Management.Smo;

    internal class SpatialProvisioning
    {
        public static void ProvisionDatabase(SqlConnection destination, SqlConnection master, string scopeName, string srid)
        {
            bool isSlave = false;
            if (!destination.ConnectionString.Equals(master.ConnectionString))
            {
                isSlave = true;
            }

            DbSyncScopeDescription scopeDescription = new DbSyncScopeDescription(scopeName);
            SqlSyncScopeProvisioning destinationConfig = new SqlSyncScopeProvisioning(destination);
            if (destinationConfig.ScopeExists(scopeName))
            {
                return;
            }

            // TODO: Retrieve actual sync tables
            IList<SpatialColumnInfo> tableList = new List<SpatialColumnInfo>();
            tableList.Add(new SpatialColumnInfo { TableName = "ProvTest" });

            if (isSlave)
            {
                destination.Open();
                foreach (SpatialColumnInfo spatialTable in tableList)
                {
                    SqlCommand command = destination.CreateCommand();
                    try
                    {
                        command.CommandText = string.Format("DROP TABLE [{0}]", spatialTable.TableName);
                        command.ExecuteNonQuery();
                    }
                    catch (SqlException ex)
                    {
                        if (ex.Message.StartsWith("Cannot drop"))
                        {
                            continue;
                        }
                    }
                }

                destination.Close();
            }

            DbSyncColumnDescription identityColumn = null;
            DbSyncColumnDescription geometryColumn = null;

            foreach (SpatialColumnInfo spatialTable in tableList)
            {
                DbSyncTableDescription table = SqlSyncDescriptionBuilder.GetDescriptionForTable(spatialTable.TableName, master);
                if (table.PkColumns.Count() != 1 || table.PkColumns.First().Type != "uniqueidentifier")
                {
                    try
                    {
                        table.Columns["UniqueID"].IsPrimaryKey = true;
                        table.PkColumns.FirstOrDefault().IsPrimaryKey = false;
                    }
                    catch (Exception)
                    {
                        throw new DataSyncException("Tables require a column called 'UniqueID' of type 'uniqueidentifier' to be used with spatial syncing." + 
                                                    "\nThe UniqueID column should also have a default value of newid() and a UNIQUE, NONCLUSTERED index.");
                    }
                }

                foreach (DbSyncColumnDescription item in table.NonPkColumns)
                {
                    if (item.AutoIncrementStepSpecified)
                    {
                        identityColumn = item;
                        spatialTable.IdentityColumn = item.UnquotedName;
                        continue;
                    }

                    if (!item.Type.Contains("geometry"))
                    {
                        continue;
                    }

                    spatialTable.GeometryColumn = item.UnquotedName;
                    geometryColumn = item;
                    geometryColumn.ParameterName += "_was_geometry";
                    geometryColumn.Type = "nvarchar";
                    geometryColumn.Size = "max";
                    geometryColumn.SizeSpecified = true;
                }

                if (geometryColumn == null || identityColumn == null)
                {
                    throw new DataSyncException("Spatial tables must contain a geometry column and an identity column.");
                }

                table.Columns.Remove(identityColumn);
                if (destination.Equals(master))
                {
                    destinationConfig.SetCreateTableDefault(DbSyncCreationOption.Skip);
                }
                else
                {
                    identityColumn.IsPrimaryKey = true;
                    destinationConfig.SetCreateTableDefault(DbSyncCreationOption.Create);
                }

                scopeDescription.Tables.Add(table);
            }

            //It is important to call this after the tables have been added to the scope
            destinationConfig.PopulateFromScopeDescription(scopeDescription);

            //provision the server
            destinationConfig.Apply();

            destination.Open();
            foreach (SpatialColumnInfo spatialTable in tableList)
            {
                string tableName = spatialTable.TableName;
                SqlCommand command = destination.CreateCommand();
                if (isSlave)
                {
                    command.CommandText = string.Format("ALTER TABLE [{0}] ADD [{1}] int IDENTITY(1,1) NOT NULL", tableName, spatialTable.IdentityColumn);
                    command.ExecuteNonQuery();
                    command.CommandText = string.Format("ALTER TABLE [{0}] DROP CONSTRAINT PK_{0}", tableName);
                    command.ExecuteNonQuery();
                    command.CommandText = string.Format("ALTER TABLE [{0}] ADD CONSTRAINT PK_{0} PRIMARY KEY CLUSTERED ([{1}])", tableName, spatialTable.IdentityColumn);
                    command.ExecuteNonQuery();
                    command.CommandText = string.Format("ALTER TABLE [{0}] ADD UNIQUE (UniqueID)", tableName);
                    command.ExecuteNonQuery();
                    command.CommandText = string.Format("ALTER TABLE [{0}] ADD CONSTRAINT [DF_{0}_UniqueID]  DEFAULT (newid()) FOR [UniqueID]", tableName);
                    command.ExecuteNonQuery();
                    command.CommandText = string.Format("ALTER TABLE [{0}] ALTER COLUMN [{1}] geometry", tableName, spatialTable.GeometryColumn);
                    command.ExecuteNonQuery();
                    command.CommandText = string.Format("CREATE SPATIAL INDEX [SIndex_{0}_{1}] ON [{0}]([{1}]) USING  GEOMETRY_GRID WITH (BOUNDING_BOX =(300000, 6700000, 500000, 7000000), GRIDS =(LEVEL_1 = MEDIUM,LEVEL_2 = MEDIUM,LEVEL_3 = MEDIUM,LEVEL_4 = MEDIUM), CELLS_PER_OBJECT = 16, PAD_INDEX  = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]", tableName, spatialTable.GeometryColumn);
                    command.ExecuteNonQuery();
                }

                try
                {
                    command.CommandText = string.Format("CREATE TRIGGER [dbo].[{0}_GEOMSRID_trigger]\nON [dbo].[{0}]\nAFTER INSERT, UPDATE\nAS UPDATE [dbo].[{0}] SET [{1}].STSrid = {2}\nFROM [dbo].[{0}]\nJOIN inserted\nON [dbo].[{0}].[UniqueID] = inserted.[UniqueID] AND inserted.[{1}] IS NOT NULL", spatialTable.TableName, spatialTable.GeometryColumn, srid);
                    command.ExecuteNonQuery();
                }
                catch (SqlException ex)
                {
                    if (!ex.Message.StartsWith("There is already"))
                    {
                        throw;
                    }
                }

                Server server = new Server(destination.DataSource);
                Database db = server.Databases[destination.Database];
                foreach (StoredProcedure sp in db.StoredProcedures.Cast<StoredProcedure>().Where(sp => sp.Name.Equals(tableName + "_selectchanges", StringComparison.InvariantCultureIgnoreCase) || sp.Name.Equals(tableName + "_selectrow", StringComparison.InvariantCultureIgnoreCase)))
                {
                    sp.TextBody = sp.TextBody.Replace(string.Format("[{0}]", spatialTable.GeometryColumn), string.Format("[{0}].STAsText() as [{0}]", spatialTable.GeometryColumn));
                    sp.Alter();
                }
            }
        }
    }
}
