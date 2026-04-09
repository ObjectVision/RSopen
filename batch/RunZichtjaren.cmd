REM ================================================================================
REM
REM Dit is RSOpen, de open source versie van het model RuimteScanner.
REM Het script wordt uitgegeven onder GNU-GPL licentie.
REM
REM RSOpen is ontwikkeld door PBL Planbureau voor de Leefomgeving,
REM i.s.m Object Vision en VU Vrije Universiteit Amsterdam.
REM Opdrachtgever/ontwikkelaar PBL: Bas van Bemmel (Bas.vanBemmel@pbl.nl)
REM Contactpersoon/ontwikkelaar Object Vision: Jip Claassens (jclaassens@objectvision.nl)
REM Contactpersoon/ontwikkelaar Deltares: Bart Rijken (bart.rijken@deltares.nl)
REM
REM Roept de allocatie per zichtjaar aan voor een gegeven scenario/variant combinatie. Afhankelijk van de
REM AlleenEindjaar-vlag worden tussenjaren (2030, 2040) overgeslagen.
REM
REM ================================================================================

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