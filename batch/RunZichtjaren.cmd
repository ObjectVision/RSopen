if "%AlleenEindjaar%" EQU "TRUE" goto runLastYear

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/Zichtjaren/Y2030/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd
call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/Zichtjaren/Y2040/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd
call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/Zichtjaren/Y2050/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd

:runLastYear

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/Zichtjaren/Y2060/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd
exit /b

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause