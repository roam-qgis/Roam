[Setup]
AppName=Roam
AppVersion=3.0.8
WizardStyle=modern
DefaultDirName=C:\Roam
DefaultGroupName=Roam
DisableProgramGroupPage=Yes
UninstallDisplayIcon={app}\Roam.exe
Compression=lzma2
SolidCompression=yes
OutputDir=..\..\Release
OutputBaseFilename=Roam Installer
LicenseFile=License.rtf

[Files]
Source: "..\..\build\exe.win-amd64-3.7\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Roam"; Filename: "{app}\Roam.exe"
