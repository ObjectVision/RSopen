REM LET OP: dit script kent het lenen van een allocatiestand NIET. Een variant die in de kolom
REM StandVanVariant van VariantParameters/VariantK.dms naar een andere variant wijst hoeft haar
REM allocatie niet te draaien, maar dit script alloceert haar toch. Gebruik voor een reeks
REM batch/Run2120.ps1; die slaat een lenende variant over en toetst bovendien of de aanname
REM eronder klopt. Zie de skill rs-draaien.

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
REM DE BATCH BEPAALT, DE CONFIGURATIE VOLGT. Instellingen die het draaien sturen worden hier gezet en via
REM omgevingsvariabelen aan de configuratie opgelegd (zie AlleenEindjaar en StandAllocatieOntkoppeld in
REM ModelParameters.dms). Dit script leest dus nooit een instelling uit de configuratie terug om te bepalen wat
REM het zelf moet doen; het weet dat al, want het heeft het zelf gezet.
REM
REM Het enige dat wel uit de configuratie komt is de LIJST zichtjaren, want die volgt uit Model_FirstZichtjaar,
REM Model_ZichtjaarInterval en Model_FinalYear en is dus modelinhoud, geen batchinstelling. Er staan hier daarom
REM geen jaartallen met naam genoemd.
REM
REM Waarom het aantal processen van StandAllocatieOntkoppeld afhangt:
REM   TRUE  Zichtjaar N+1 leest de stand van zichtjaar N terug uit een tif (Templates/Allocatie/Zichtjaar_T,
REM         StateNaAllocatie). GeoDMS bindt storage bij het LADEN van de configuratie, dus een tif die er bij
REM         het laden nog niet is blijft in datzelfde proces onleesbaar. Elk zichtjaar krijgt daarom een eigen
REM         proces. Voordeel: het geheugengebruik blijft begrensd en na een fout kan vanaf het laatste
REM         geslaagde zichtjaar worden doorgestart.
REM   FALSE De stand blijft in het geheugen. Alleen het laatste zichtjaar wordt aangeroepen; de
REM         padafhankelijkheid trekt de eerdere zichtjaren binnen datzelfde proces vanzelf mee. Ze hier stuk
REM         voor stuk aanroepen zou elk vorig zichtjaar per proces opnieuw uitrekenen.
REM
REM ================================================================================

setlocal EnableExtensions EnableDelayedExpansion

REM Default zodat dit script ook los aanroepbaar blijft. RunAll.cmd hoort deze te zetten.
if "%StandAllocatieOntkoppeld%" EQU "" set StandAllocatieOntkoppeld=TRUE

REM Forward slashes, zodat het pad zowel voor cmd als voor GeoDMS werkt. De map batch/log staat in .gitignore
REM en bevat ook de overige batchlogs.
set RSO_ZICHTJARENFILE=%ProjDir:\=/%/batch/log/zichtjaren.txt

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /BatchOndersteuning/Zichtjaren
if %ErrorLevel% NEQ 0 goto ErrorEnd

set ZICHTJAREN=
set /p ZICHTJAREN=<"%RSO_ZICHTJARENFILE%"
if "%ZICHTJAREN%" EQU "" (
	echo "Geen zichtjaren gevonden in %RSO_ZICHTJARENFILE%"
	goto ErrorEnd
)

if "%StandAllocatieOntkoppeld%" EQU "FALSE" goto EenProces

echo Ontkoppeld, dus een proces per zichtjaar: %ZICHTJAREN%
for %%J in (%ZICHTJAREN%) do (
	call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Zichtjaren/%%J/Impl/Generate
	if !ErrorLevel! NEQ 0 goto ErrorEnd
)
goto Klaar

:EenProces
REM Niet ontkoppeld: alleen het laatste zichtjaar aanroepen, de rest volgt binnen hetzelfde proces.
for %%J in (%ZICHTJAREN%) do set LAATSTE=%%J
echo Niet ontkoppeld, dus alles in een proces via het laatste zichtjaar: %LAATSTE%
call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms Allocatie/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Zichtjaren/%LAATSTE%/Impl/Generate
if %ErrorLevel% NEQ 0 goto ErrorEnd

:Klaar

REM De indicatoren draaien in een eigen proces met StandAllocatieOntkoppeld op TRUE, zodat ze de stand uit de
REM zojuist geschreven tifs lezen. Zonder die schakelaar zou dit tweede proces de hele allocatie opnieuw
REM uitrekenen, want GeoDMS bewaart niets tussen processen. De aanroep stond hier tot #714 uitgecommentarieerd
REM en wees bovendien naar /Indicatoren/Export, een pad dat niet bestaat: het casusniveau ontbrak en de
REM container Export hangt onder Zichtjaren.
REM
REM Generate_Indicatoren schrijft precies een zichtjaar, standaard het laatste. Wie ook de tussenliggende
REM zichtjaren wil wegschrijven zet de omgevingsvariabele ExportZichtjaar en roept dit per jaar aan; dat doet
REM batch\RunIndicatoren.ps1, dat over varianten en zichtjaren heen loopt. De TRUE hieronder geldt alleen binnen
REM dit script (setlocal); RunAll.cmd bepaalt de waarde voor de allocatie hierboven.
set StandAllocatieOntkoppeld=TRUE
call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Zichtjaren/Export/Generate_Indicatoren
if %ErrorLevel% NEQ 0 goto ErrorEnd

REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /Indicatoren/%RSL_SCENARIO_NAME%_%RSL_VARIANT_NAME%/Basisjaar/Landgebruikskaart/Result_SA
REM if %ErrorLevel% NEQ 0 goto ErrorEnd

endlocal
exit /b

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause
