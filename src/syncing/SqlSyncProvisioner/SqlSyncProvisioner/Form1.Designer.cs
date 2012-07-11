namespace SqlSyncProvisioner
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.provisionMasterButton = new System.Windows.Forms.Button();
            this.scopeNameTextBox = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.deprovisionMasterButton = new System.Windows.Forms.Button();
            this.provisionClientButton = new System.Windows.Forms.Button();
            this.deprovisionClientButton = new System.Windows.Forms.Button();
            this.sridTextBox = new System.Windows.Forms.TextBox();
            this.sridLabel = new System.Windows.Forms.Label();
            this.SuspendLayout();
            // 
            // provisionMasterButton
            // 
            this.provisionMasterButton.Location = new System.Drawing.Point(148, 82);
            this.provisionMasterButton.Name = "provisionMasterButton";
            this.provisionMasterButton.Size = new System.Drawing.Size(116, 23);
            this.provisionMasterButton.TabIndex = 0;
            this.provisionMasterButton.Text = "Provision &Master";
            this.provisionMasterButton.UseVisualStyleBackColor = true;
            this.provisionMasterButton.Click += new System.EventHandler(this.ProvisionMasterButton_Click);
            // 
            // scopeNameTextBox
            // 
            this.scopeNameTextBox.Location = new System.Drawing.Point(148, 21);
            this.scopeNameTextBox.Name = "scopeNameTextBox";
            this.scopeNameTextBox.Size = new System.Drawing.Size(116, 20);
            this.scopeNameTextBox.TabIndex = 1;
            // 
            // label1
            // 
            this.label1.Location = new System.Drawing.Point(42, 19);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(100, 23);
            this.label1.TabIndex = 2;
            this.label1.Text = "Scope Name:";
            this.label1.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
            // 
            // deprovisionMasterButton
            // 
            this.deprovisionMasterButton.Location = new System.Drawing.Point(302, 82);
            this.deprovisionMasterButton.Name = "deprovisionMasterButton";
            this.deprovisionMasterButton.Size = new System.Drawing.Size(116, 23);
            this.deprovisionMasterButton.TabIndex = 3;
            this.deprovisionMasterButton.Text = "Deprovision Master";
            this.deprovisionMasterButton.UseVisualStyleBackColor = true;
            this.deprovisionMasterButton.Click += new System.EventHandler(this.DeprovisionMasterButton_Click);
            // 
            // provisionClientButton
            // 
            this.provisionClientButton.Location = new System.Drawing.Point(148, 147);
            this.provisionClientButton.Name = "provisionClientButton";
            this.provisionClientButton.Size = new System.Drawing.Size(116, 23);
            this.provisionClientButton.TabIndex = 4;
            this.provisionClientButton.Text = "Provision &Client";
            this.provisionClientButton.UseVisualStyleBackColor = true;
            this.provisionClientButton.Click += new System.EventHandler(this.ProvisionClientButton_Click);
            // 
            // deprovisionClientButton
            // 
            this.deprovisionClientButton.Location = new System.Drawing.Point(302, 147);
            this.deprovisionClientButton.Name = "deprovisionClientButton";
            this.deprovisionClientButton.Size = new System.Drawing.Size(116, 23);
            this.deprovisionClientButton.TabIndex = 5;
            this.deprovisionClientButton.Text = "Deprovision C&lient";
            this.deprovisionClientButton.UseVisualStyleBackColor = true;
            this.deprovisionClientButton.Click += new System.EventHandler(this.DeprovisionClientButton_Click);
            // 
            // sridTextBox
            // 
            this.sridTextBox.Location = new System.Drawing.Point(578, 258);
            this.sridTextBox.Name = "sridTextBox";
            this.sridTextBox.Size = new System.Drawing.Size(116, 20);
            this.sridTextBox.TabIndex = 6;
            this.sridTextBox.Text = "28356";
            // 
            // sridLabel
            // 
            this.sridLabel.Location = new System.Drawing.Point(472, 256);
            this.sridLabel.Name = "sridLabel";
            this.sridLabel.Size = new System.Drawing.Size(100, 23);
            this.sridLabel.TabIndex = 7;
            this.sridLabel.Text = "SRID:";
            this.sridLabel.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(706, 290);
            this.Controls.Add(this.sridLabel);
            this.Controls.Add(this.sridTextBox);
            this.Controls.Add(this.deprovisionClientButton);
            this.Controls.Add(this.provisionClientButton);
            this.Controls.Add(this.deprovisionMasterButton);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.scopeNameTextBox);
            this.Controls.Add(this.provisionMasterButton);
            this.Name = "Form1";
            this.Text = "Form1";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Button provisionMasterButton;
        private System.Windows.Forms.TextBox scopeNameTextBox;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Button deprovisionMasterButton;
        private System.Windows.Forms.Button provisionClientButton;
        private System.Windows.Forms.Button deprovisionClientButton;
        private System.Windows.Forms.TextBox sridTextBox;
        private System.Windows.Forms.Label sridLabel;
    }
}

