using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;
using System.Data.SqlClient;

namespace SqlSyncProvisioner
{
    static class Program
    {
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new Form1());
                return;
            }

            
            string connectionstring = "Data Source={0};Initial Catalog={1};Integrated Security=SSPI;";
            SqlConnection server = new SqlConnection();
            SqlConnection client = new SqlConnection();
            List<String> scopes;
            bool provison_server;
            bool provison_client;
            bool deprovison_server;
            bool deprovison_client;
            foreach (var arg in args)
            {
                var pairs = arg.Split('=');
                var name = pairs[0];
                string[] parms = pairs[1].Split('|');
                string conn = "";
                switch (name)
	            {
                    case "--server":
                        conn = String.Format(connectionstring, parms[0], parms[1]);
                        server.ConnectionString = conn;
                        break;
                    case "--client":
                        conn = String.Format(connectionstring, parms[0], parms[1]);
                        client.ConnectionString = conn;
                        break;
                    case "--scopes":
                        scopes = parms.ToList();
                        break;
                    case "--provision":
                        provison_server = parms.Contains("server");
                        provison_client = parms.Contains("client");
                        break;
                    case "--deprovision":
                        deprovison_server = parms.Contains("server");
                        deprovison_client = parms.Contains("client");
                        break;
		            default:
                        break;
	            }
            }

            Console.WriteLine(args);
        }
    }
}
