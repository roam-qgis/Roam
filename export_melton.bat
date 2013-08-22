@ECHO OFF

: Export QMap for client side install

SET NAME=Melton Install

call baseexport.bat

: Over write the project file with the template one

SET PROJECT=%HOME%\projects\melton_firebreak
move /Y "%PROJECT%\_docs\*" "%HOME%\docs\"


