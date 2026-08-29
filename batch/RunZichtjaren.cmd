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

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Impl/Generate_LastZichtjaar
if %ErrorLevel% NEQ 0 goto ErrorEnd

REM De indicatoren draaien in een eigen proces met StandAllocatieOntkoppeld op TRUE, zodat ze de stand uit de
REM zojuist geschreven tifs lezen. Zonder die schakelaar zou dit tweede proces de hele allocatie opnieuw
REM uitrekenen, want GeoDMS bewaart niets tussen processen. De aanroep stond hier tot #714 uitgecommentarieerd
REM en wees bovendien naar /Indicatoren/Export, een pad dat niet bestaat: het casusniveau ontbrak en de
REM container Export hangt onder Zichtjaren.
REM
REM Generate_Indicatoren schrijft precies een zichtjaar, standaard het laatste. Wie ook de tussenliggende
REM zichtjaren wil wegschrijven zet de omgevingsvariabele ExportZichtjaar en roept dit per jaar aan; dat doet
REM batch\RunIndicatoren.ps1, dat over varianten en zichtjaren heen loopt.
set StandAllocatieOntkoppeld=TRUE
call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Zichtjaren/Export/Generate_Indicatoren
if %ErrorLevel% NEQ 0 goto ErrorEnd
set StandAllocatieOntkoppeld=FALSE

REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Basisjaar/Landgebruikskaart/Result_SA
REM if %ErrorLevel% NEQ 0 goto ErrorEnd

exit /b

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause
