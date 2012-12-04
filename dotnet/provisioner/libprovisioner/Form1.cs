
namespace SqlSyncProvisioner
{
    using System;
    using System.Data.SqlClient;
    using System.Drawing;
    using System.Windows.Forms;
    using Microsoft.Synchronization;
    using Microsoft.Synchronization.Data.SqlServer;
    using Properties;

    public partial class Form1 : Form
    {
        private const string TableName = "AddressNumbers"; 

        public Form1()
        {
            this.InitializeComponent();
            base.Font = SystemFonts.IconTitleFont;
        }

        private void ProvisionMasterButton_Click(object sender, EventArgs e)
        {
            using (SqlConnection master = new SqlConnection(Settings.Default.MasterConnectionString))
            {
                try
                {
                    // SpatialProvisioning.ProvisionDatabase(master, master, this.scopeNameTextBox.Text, this.sridTextBox.Text);
                    TableProvisioning.ProvisionTable(master, master, TableName, int.Parse(this.sridTextBox.Text), false);
                    MessageBox.Show("Database successfully provisioned for syncing.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
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
                    using (SqlCommand command = master.CreateCommand())
                    {
                        master.Open();
                        command.CommandText = string.Format("IF EXISTS (SELECT * FROM sys.triggers WHERE object_id = OBJECT_ID(N'[dbo].[{0}_GEOMSRID_trigger]')) DROP TRIGGER [dbo].[{0}_GEOMSRID_trigger]", TableName);
                        command.ExecuteNonQuery();
                        master.Close();
                    }

                    MessageBox.Show("Database successfully deprovisioned.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception exception)
                {
                    MessageBox.Show(exception.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void ProvisionClientButton_Click(object sender, EventArgs e)
        {
            using (SqlConnection master = new SqlConnection(Settings.Default.MasterConnectionString), slave = new SqlConnection(Settings.Default.SlaveConnectionString))
            {
                try
                {
                    using (SqlCommand command = slave.CreateCommand())
                    {
                        slave.Open();
                        command.CommandText = string.Format("IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{0}]') AND type in (N'U')) DROP TABLE [dbo].[{0}]", TableName);
                        command.ExecuteNonQuery();
                        slave.Close();
                    }

                    // SpatialProvisioning.ProvisionDatabase(slave, master, this.scopeNameTextBox.Text, this.sridTextBox.Text);
                    TableProvisioning.ProvisionTable(master, slave, TableName, int.Parse(this.sridTextBox.Text), false);
                    MessageBox.Show("Database successfully provisioned for syncing.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
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
                    using (SqlCommand command = slave.CreateCommand())
                    {
                        slave.Open();
                        command.CommandText = string.Format("IF EXISTS (SELECT * FROM sys.triggers WHERE object_id = OBJECT_ID(N'[dbo].[{0}_GEOMSRID_trigger]')) DROP TRIGGER [dbo].[{0}_GEOMSRID_trigger]", TableName);
                        command.ExecuteNonQuery();
                        slave.Close();
                    }

                    MessageBox.Show("Database successfully deprovisioned.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception exception)
                {
                    MessageBox.Show(exception.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }

        }

        private void syncButton_Click(object sender, EventArgs e)
        {
            using (SqlSyncProvider masterProvider = new SqlSyncProvider { ScopeName = this.scopeNameTextBox.Text }, slaveProvider = new SqlSyncProvider { ScopeName = this.scopeNameTextBox.Text })
            {
                using (SqlConnection master = new SqlConnection(Settings.Default.MasterConnectionString), slave = new SqlConnection(Settings.Default.SlaveConnectionString))
                {
                    string masterScopeConfig;
                    string slaveScopeConfig;

                    using (SqlCommand command = master.CreateCommand())
                    {
                        master.Open();
                        command.CommandText = string.Format("SELECT scope_config.config_data FROM scope_config INNER JOIN scope_info ON scope_config.config_id = scope_info.scope_config_id WHERE scope_info.sync_scope_name = N'{0}'", TableName);
                        masterScopeConfig = command.ExecuteScalar() as string;
                        master.Close();
                    }

                    using (SqlCommand command = slave.CreateCommand())
                    {
                        slave.Open();
                        command.CommandText = string.Format("SELECT scope_config.config_data FROM scope_config INNER JOIN scope_info ON scope_config.config_id = scope_info.scope_config_id WHERE scope_info.sync_scope_name = N'{0}'", TableName);
                        slaveScopeConfig = command.ExecuteScalar() as string;
                        slave.Close();
                    }

                    if (masterScopeConfig != slaveScopeConfig)
                    {
                        MessageBox.Show("The master scope does not match the slave scope", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        return;
                    }

                    masterProvider.Connection = master;
                    slaveProvider.Connection = slave;
                    SyncOrchestrator orchestrator = new SyncOrchestrator
                                                        {
                                                            LocalProvider = slaveProvider,
                                                            RemoteProvider = masterProvider,
                                                            Direction = SyncDirectionOrder.UploadAndDownload
                                                        };

                    try
                    {
                        SyncOperationStatistics stats = orchestrator.Synchronize();
                        MessageBox.Show("Downloaded: " + stats.DownloadChangesTotal + "Uploaded: " + stats.UploadChangesApplied, "Complete", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show(ex.Message, "Sync Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
        }
    }
}
