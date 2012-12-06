using System.Data.SqlClient;
using Microsoft.Synchronization.Data.SqlServer;
public static class Deprovisioning
{
    /// <summary>
    /// Drop the table from the database if it exists.
    /// </summary>
    /// <param name="conn">Connection to the database</param>
    /// <param name="table">The table to drop.</param>
    public static void DropTable(SqlConnection conn, string table)
    {
        string sql = @"IF (EXISTS (SELECT * 
                             FROM INFORMATION_SCHEMA.TABLES 
                             WHERE TABLE_SCHEMA = 'dbo' 
                             AND TABLE_NAME = @table))
                          DROP TABLE @table";

        using (SqlCommand command = conn.CreateCommand())
        {
            conn.Open();
            command.CommandText = sql;
            command.Parameters.Add("@table", table);
            command.ExecuteNonQuery();
            conn.Close();
        }
    
    }

    /// <summary>
    /// Drop the GEOM SRID correction trigger from the table.
    /// </summary>
    /// <param name="conn"></param>
    /// <param name="table"></param>
    public static void DropTableGeomTrigger(SqlConnection conn, string table)
    {
        string sql = @"IF EXISTS (SELECT * 
                                      FROM sys.triggers 
                                      WHERE object_id = OBJECT_ID(N'[dbo].[{0}_GEOMSRID_trigger]')) 
                           DROP TRIGGER [dbo].[{0}_GEOMSRID_trigger]";

        using (SqlCommand command = conn.CreateCommand())
        {
            conn.Open();
            command.CommandText = string.Format(sql, table);
            command.ExecuteNonQuery();
            conn.Close();
        }
    }

    /// <summary>
    /// Deprovsions the scope from the database. 
    /// </summary>
    /// <param name="conn"></param>
    /// <param name="scope"></param>
    /// <returns></returns>
    public static void DeprovisonScope(SqlConnection conn, string scope)
    {
        SqlSyncScopeDeprovisioning prov = new SqlSyncScopeDeprovisioning(conn);
        prov.DeprovisionScope(scope);
    }
}