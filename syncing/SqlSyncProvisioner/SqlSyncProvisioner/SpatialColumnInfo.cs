namespace SqlSyncProvisioner
{
    internal class SpatialColumnInfo
    {
        public string TableName { get; set; }

        public string IdentityColumn { get; set; }

        public string GeometryColumn { get; set; }
    }
}
