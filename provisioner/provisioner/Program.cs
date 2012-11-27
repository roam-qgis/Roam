using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Data.SqlClient;

namespace ConsoleApplication1
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(args.Length);

            string connectionstring = "Data Source={0};Initial Catalog={1};Integrated Security=SSPI;";
            SqlConnection server = new SqlConnection();
            SqlConnection client = new SqlConnection();
            string serverconn = "";
            string clientconn = "";
            bool deprovison = false;
            string tablename = "";
            string direction = "OneWay";

            bool hasserver = args.Any(x => x.Contains("--server"));
            if (!hasserver)
            {
                Console.Error.WriteLine("We need a server connection string");
                return;
            }

            // If there is no client arg given then we assume that we are talking
            // working on the server tables
            bool hastable = args.Any(x => x.Contains("--table"));
            if (!hastable)
            {
                Console.Error.WriteLine("We need a table to work on");
                Console.Read();
                return;
            }

            foreach (var arg in args)
            {
                Console.WriteLine(arg);
                var pairs = arg.Split(new char[] { '=' }, 2,
                                      StringSplitOptions.None);
                var name = pairs[0];
                string parm = pairs[1];
                switch (name)
                {
                    case "--server":
                        serverconn = parm;
                        server.ConnectionString = parm;
                        break;
                    case "--client":
                        clientconn = parm;
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
            bool hasclient = args.Any(x => x.Contains("--client"));
            if (!hasclient)
            {
                client = server;
                Console.WriteLine("No client given. Client is now server connection");
            }

            Console.WriteLine("\n\r");

            Console.WriteLine("Running using these settings");
            Console.WriteLine("Server:" + server.ConnectionString);
            Console.WriteLine("Client:" + client.ConnectionString);
            Console.WriteLine("Table:" + tablename);
            Console.WriteLine("Direction:" + direction);
            Console.WriteLine("Mode:" + (deprovison ? "Deprovison" : "Provision"));
        }
    }
}
