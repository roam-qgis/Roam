REM setup.exe /Q /CONFIGURATIONFILE="ConfigurationFile.ini" /IACCEPTSQLSERVERLICENSETERMS
REM netsh advfirewall firewall add rule name="SQLServer" dir=in action=allow protocol=TCP localport=1433 profile=DOMAIN
REGEDIT /s FieldDataDSN.reg
SQLCMD -S localhost  -Q "CREATE DATABASE FieldData" 