namespace SqlSyncProvisioner
{
    using System;
    using System.Data.SqlClient;
    using System.Drawing;
    using System.Windows.Forms;
    using Microsoft.Synchronization.Data.SqlServer;
    using Properties;

    public partial class Form1 : Form
    {
        public Form1()
        {
            this.InitializeComponent();
            this.Font = SystemFonts.IconTitleFont;
        }

        private void ProvisionMasterButton_Click(object sender, EventArgs e)
        {
            using (SqlConnection master = new SqlConnection(Settings.Default.MasterConnectionString))
            {
                try
                {
                    SpatialProvisioning.ProvisionDatabase(master, master, this.scopeNameTextBox.Text, this.sridTextBox.Text);
                    MessageBox.Show(@"Database successfully provisioned for syncing.", @"Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception exception)
                {
                    MessageBox.Show(exception.Message, @"Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void DeprovisionMasterButton_Click(object sender, EventArgs e)
        {
            using (SqlConnection master = new SqlConnection(Settings.Default.MasterConnectionString))
            {
                try
                {
                    SqlSyncScopeDeprovisioning prov = new SqlSyncScopeDeprovisioning(master);
                    prov.DeprovisionScope(this.scopeNameTextBox.Text);
                    MessageBox.Show(@"Database successfully deprovisioned.", @"Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception exception)
                {
                    MessageBox.Show(exception.Message, @"Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void ProvisionClientButton_Click(object sender, EventArgs e)
        {
            using (SqlConnection master = new SqlConnection(Settings.Default.MasterConnectionString), slave = new SqlConnection(Settings.Default.SlaveConnectionString))
            {
                try
                {
                    SpatialProvisioning.ProvisionDatabase(slave, master, this.scopeNameTextBox.Text, this.sridTextBox.Text);
                    MessageBox.Show(@"Database successfully provisioned for syncing.", @"Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception exception)
                {
                    MessageBox.Show(exception.Message, @"Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void DeprovisionClientButton_Click(object sender, EventArgs e)
        {
            using (SqlConnection slave = new SqlConnection(Settings.Default.SlaveConnectionString))
            {
                try
                {
                    SqlSyncScopeDeprovisioning prov = new SqlSyncScopeDeprovisioning(slave);
                    prov.DeprovisionScope(this.scopeNameTextBox.Text);
                    MessageBox.Show(@"Database successfully deprovisioned.", @"Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception exception)
                {
                    MessageBox.Show(exception.Message, @"Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }

        }
    }
}
