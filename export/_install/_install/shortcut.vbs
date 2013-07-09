set WshShell = WScript.CreateObject("WScript.Shell" )
strDesktop = WshShell.SpecialFolders("AllUsersDesktop" )
set oShellLink = WshShell.CreateShortcut(strDesktop & "\IntraMaps Roam.lnk" )
oShellLink.TargetPath = "C:\IntraMaps Roam\IntraMaps Roam.bat"
oShellLink.IconLocation = "C:\IntraMaps Roam\icon.ico"
oShellLink.WindowStyle = 1
oShellLink.Description = "IntraMaps Roam"
oShellLink.WorkingDirectory = "C:\IntraMaps Roam"
oShellLink.Save