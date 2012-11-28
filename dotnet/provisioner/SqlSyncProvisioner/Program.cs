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
            //if (args.Length == 0)
            //{
            //    Application.EnableVisualStyles();
            //    Application.SetCompatibleTextRenderingDefault(false);
            //    Application.Run(new Form1());
            //    return;
            //}

 
            string connectionstring = "Data Source={0};Initial Catalog={1};Integrated Security=SSPI;";
            SqlConnection server = new SqlConnection();
            SqlConnection client = new SqlConnection();
            bool deprovison;
            string tablename;
            string direction;

            Console.WriteLine(args);

            // If there is no client arg given then we assume that we are talking
            // working on the server tables
            if (!args.Contains("--table"))
            {
                Console.Error.WriteLine("We need a table to work on");
                return;
            }

            foreach (var arg in args)
            {
                var pairs = arg.Split(new char[] { '=' }, 2, 
                                      StringSplitOptions.None);
                var name = pairs[0];
                string parm = pairs[1];
                switch (name)
	            {
                    case "--server":
                        server.ConnectionString = parm;
                        break;
                    case "--client":
                        client.ConnectionString = parm;
                        break;
                    case "--table":
                        tablename = parm;
                        break;
                    case "--direction":
                        direction = parm;
                        break;
                    case "--deprovision":
                        deprovison = true;
                        break;
		            default:
                        break;
	            }
            }

            // If there is no client arg given then we assume that we are talking
            // working on the server tables
            if (!args.Contains("--client"))
            {
                client = server;
            }

            Console.WriteLine(args);
        }
    }
}
