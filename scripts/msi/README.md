## QGIS MSI Package Scripts

This respositry contains scripts that can be used to create a MSI installer package for QGIS 2.14 and above.

### Requirments

- WiX MSI toolkit (http://wixtoolset.org/releases/)
- QGIS Installed in ..\ to these scripts (adjust `%BASE%` in batch files if not)

### Scripts

- `buid.bat` - Creates a 2.14 installer package
- `collectfiles.bat` - WiX scripts to collect all the files from the `%BASE%`. Called by `build.bat`

### Output

- `QGIS 2.14.msi` - Installs into ProgramFiles64Folder with shortcuts on desktop and start menu
