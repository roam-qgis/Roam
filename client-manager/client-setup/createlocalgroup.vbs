Set network = WScript.CreateObject( "WScript.Network" )
computer_name = network.ComputerName
WScript.Echo "Computer Name: " & computer_name

REM strComputer = "MyComputer"
REM Set colAccounts = GetObject("WinNT://" & strComputer & "")
REM Set objUser = colAccounts.Create("group", "FinanceUsers")
REM objUser.SetInfo