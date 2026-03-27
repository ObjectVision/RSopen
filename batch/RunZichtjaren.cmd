if "%AlleenEindjaar%" EQU "TRUE" goto runLastYear

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Zichtjaren/Y2030/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd
call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Zichtjaren/Y2040/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd

REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/Basisjaar/Landgebruikskaart/Result_SA
REM if %ErrorLevel% NEQ 0 goto ErrorEnd
REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/Y2030/Landgebruikskaart/Result_SA
REM if %ErrorLevel% NEQ 0 goto ErrorEnd
REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/Y2040/Landgebruikskaart/Result_SA
REM if %ErrorLevel% NEQ 0 goto ErrorEnd


:runLastYear

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Zichtjaren/Y2050/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd

REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/Export/Generate_Indicatoren
REM if %ErrorLevel% NEQ 0 goto ErrorEnd

exit /b

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause