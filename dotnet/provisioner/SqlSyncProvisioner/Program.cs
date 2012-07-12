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

            var splitargs = new Dictionary<string, List<string>>();

            foreach (var arg in args)
            {
                var pairs = arg.Split('=');
                var name = pairs[0];
                var parms = pairs[1].Split('|');
                splitargs.Add(name, parms.ToList());
            }

            switch (splitargs.Keys)
	{
		default:
 break;
	}

            string connectionstring = String.Format("Data Source=SD0469;Initial Catalog=FieldData;Integrated Security=SSPI;");

            Console.WriteLine(args);
        }
    }
}
