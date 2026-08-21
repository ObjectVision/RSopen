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
REM Roept de allocatie aan voor een gegeven scenario/variant combinatie.
REM
REM Er staat hier bewust geen enkel jaartal en ook geen lijst zichtjaren. De batch vraagt om
REM Generate_LastZichtjaar en de configuratie zoekt het laatste zichtjaar zelf op met last(), zodat de set
REM zichtjaren volledig uit Model_FinalYear en AlleenEindjaar volgt (pbl-nl/model-RSopen#37).
REM
REM Een aanroep volstaat omdat RunAll.cmd StandAllocatieOntkoppeld op FALSE zet: de stand blijft dan in het
REM geheugen en de padafhankelijkheid trekt de eerdere zichtjaren binnen hetzelfde proces mee. De stand-tifs
REM worden daarbij nog steeds geschreven (zie WriteStand in Templates/Allocatie/Zichtjaar_T.dms), dus de
REM indicatoren en de GUI kunnen er daarna gewoon mee verder.
REM
REM ================================================================================

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Generate_LastZichtjaar
if %ErrorLevel% NEQ 0 goto ErrorEnd

REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/Basisjaar/Landgebruikskaart/Result_SA
REM if %ErrorLevel% NEQ 0 goto ErrorEnd

REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/Export/Generate_Indicatoren
REM if %ErrorLevel% NEQ 0 goto ErrorEnd

exit /b

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause
