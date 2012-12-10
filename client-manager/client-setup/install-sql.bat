cd /d %~dp0

setup.exe /Q /CONFIGURATIONFILE="ConfigurationFile.ini" /IACCEPTSQLSERVERLICENSETERMS
netsh advfirewall firewall add rule name="SQLServer" dir=in action=allow protocol=TCP localport=1433 profile=DOMAIN
REGEDIT /s FieldDataDSN.reg
SQLCMD -S localhost  -Q "CREATE DATABASE FieldData" 

msiexec /i "Sync Framework 2.1\Synchronization-v2.1-x86-ENU.msi"/passive /norestart
msiexec /i "Sync Framework 2.1\ProviderServices-v2.1-x86-ENU.msi"/passive /norestart  
msiexec /i "Sync Framework 2.1\DatabaseProviders-v3.1-x86-ENU.msi" /passive /norestart