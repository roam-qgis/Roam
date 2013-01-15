using System.Data.SqlClient;
using Microsoft.Synchronization.Data.SqlServer;
using Microsoft.Synchronization.Data;
using System;

public static class Deprovisioning
{
    /// <summary>
    /// Drop the table from the database if it exists.
    /// </summary>
    /// <param name="conn">Connection to the database</param>
    /// <param name="table">The table to drop.</param>
    public static void DropTable(SqlConnection conn, string table)
    {
        string sql = string.Format(@"IF (EXISTS (SELECT * 
                             FROM INFORMATION_SCHEMA.TABLES 
                             WHERE TABLE_SCHEMA = 'dbo' 
                             AND TABLE_NAME = '{0}'))
                          DROP TABLE [{0}]",table);

        using (SqlCommand command = conn.CreateCommand())
        {
            command.CommandText = sql;
            command.ExecuteNonQuery();
        }
    }

    public static void RemoveFromScopesTable(SqlConnection conn, string scope)
    {
        string sql = string.Format(@"DELETE FROM [scopes]
                       WHERE scope = {0}", scope);
        SqlCommand command = conn.CreateCommand();
        command.CommandText = sql;
        command.ExecuteNonQuery();
    }

    /// <summary>
    /// Drop the GEOM SRID correction trigger from the table.
    /// </summary>
    /// <param name="conn"></param>
    /// <param name="table"></param>
    public static void DropTableGeomTrigger(SqlConnection conn, string table)
    {
        string sql = @"IF (EXISTS (SELECT * 
                                  FROM sys.triggers 
                                  WHERE object_id = OBJECT_ID(N'[dbo].[{0}_GEOMSRID_trigger]')))
                           DROP TRIGGER [dbo].[{0}_GEOMSRID_trigger]";

        using (SqlCommand command = conn.CreateCommand())
        {
            command.CommandText = string.Format(sql, table);
            command.ExecuteNonQuery();
        }
    }

    /// <summary>
    /// Deprovsions the scope from the database. 
    /// </summary>
    /// <param name="conn"></param>
    /// <param name="scope"></param>
    /// <returns></returns>
    public static bool DeprovisonScope(SqlConnection conn, string scope)
    {
        conn.Open();
        SqlSyncScopeDeprovisioning prov = new SqlSyncScopeDeprovisioning(conn);
        try
        {
            prov.DeprovisionScope(scope);
            DropTableGeomTrigger(conn, scope);
        }
        catch (DbSyncException ex)
        {
            ConsoleColor color = Console.ForegroundColor;
            Console.ForegroundColor = ConsoleColor.Red;
            Console.Error.WriteLine(ex.Message);
            Console.ForegroundColor = color;
            return false;
        }
        conn.Close();
        return true;
    }
}