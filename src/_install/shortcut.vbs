set WshShell = WScript.CreateObject("WScript.Shell" )
Set oFSO = CreateObject("Scripting.FileSystemObject")

strDesktop = WshShell.SpecialFolders("AllUsersDesktop" )
strStartMenu = WshShell.SpecialFolders("AllUsersStartmenu" )

dim target
dim icon
dim style
dim description
dim working

If Not oFSO.FolderExists(strStartMenu & "\Programs\IntraMaps Roam") Then
  oFSO.CreateFolder strStartMenu & "\Programs\IntraMaps Roam"
End If

set oDesktopShellLink = WshShell.CreateShortcut(strDesktop & "\IntraMaps Roam.lnk" )
set oStartShellLink = WshShell.CreateShortcut(strStartMenu & "\Programs\IntraMaps Roam\IntraMaps Roam.lnk" )
set oStartDocsShellLink = WshShell.CreateShortcut(strStartMenu & "\Programs\IntraMaps Roam\help.lnk" )

target = "C:\IntraMaps Roam\IntraMaps Roam.bat"
icon = "C:\IntraMaps Roam\icon.ico"
style = 1
description = "IntraMaps Roam"
working = "C:\IntraMaps Roam"

oDesktopShellLink.TargetPath = target
oDesktopShellLink.IconLocation = icon
oDesktopShellLink.WindowStyle = 1
oDesktopShellLink.Description = description
oDesktopShellLink.WorkingDirectory = working
oDesktopShellLink.Save

oStartShellLink.TargetPath = target
oStartShellLink.IconLocation = icon
oStartShellLink.WindowStyle = style
oStartShellLink.Description = description
oStartShellLink.WorkingDirectory = working
oStartShellLink.Save

oStartDocsShellLink.TargetPath = "C:\IntraMaps Roam\docs\"
oStartDocsShellLink.WindowStyle = style
oStartDocsShellLink.Description = "IntraMaps Roam Documentation"
oStartDocsShellLink.WorkingDirectory = "C:\IntraMaps Roam\docs"
oStartDocsShellLink.Save