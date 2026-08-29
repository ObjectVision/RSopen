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
REM Start een volledige RSopen modelrun: stelt paden en GeoDMS-versie in, vraagt of basedata hergebruikt kan
REM worden en of alleen het eindjaar berekend moet worden, en roept daarna de deelscripts (PrepareBasedata,
REM RunScenarios, RunVariantData) aan.
REM
REM ================================================================================

REM ========== PARAMETER INSTELLINGEN ================
REM De geinstalleerde GeoDMS, niet de build uit Visual Studio. Die laatste is een bewegend doel:
REM hij wordt opnieuw gecompileerd zonder dat de configuratie verandert, en een run kan dan
REM halverwege op een andere engine draaien dan waarmee hij begon.
set geodmsversion=GeoDms20.17.0.m
set exe_dir=C:\Program Files\ObjectVision\%geodmsversion%
REM set exe_dir=C:\dev\GeoDms_2026\bin\Release\x64
set ProgramPath=%exe_dir%\GeoDmsRun.exe
REM set LocalDataProjDir=K:\LD\RSOpen
set LocalDataProjDir=C:\LocalData\RSopen

set MT_FLAGS=/S1 /S2 /S3

REM Overrulet ModelParameters/StandAllocatieOntkoppeld. Dit is een BATCH-instelling.
REM FALSE: alle zichtjaren in een proces. De stand blijft in het geheugen en de padafhankelijkheid trekt de
REM        eerdere zichtjaren mee, dus de batch vraagt alleen om het laatste zichtjaar. De stand-tifs worden
REM        nog steeds geschreven, dus de indicatoren en de GUI kunnen er daarna mee verder.
REM TRUE:  zichtjaar N+1 leest de stand van N terug uit een tif. Omdat GeoDMS storage bij het laden bindt heeft
REM        elk zichtjaar dan een eigen proces nodig, en dat kan dit script niet meer regelen. Zet deze waarde
REM        dus alleen op TRUE als het geheugen de hele keten niet aankan, en roep de zichtjaren dan met de hand
REM        stuk voor stuk aan.
set StandAllocatieOntkoppeld=FALSE

set CurrentDir=%CD%
CD ..
set ProjDir=%CD%
CD %CurrentDir%
REM ========= EINDE PARAMETER INSTELLINGEN ===========

REM deletes the old log file; each run adds the timed version to it.
del log\log.txt

REM Default is sequentieel doorrekenen, dus alle zichtjaren. De padafhankelijkheid doet dan mee, en dat is
REM nodig voor onder meer de geschiktheid voor wonen: die gebruikt de natuur en het water die aan het begin
REM van een zichtjaar liggen, en dat kan alleen als de tussenliggende zichtjaren echt doorgerekend worden (#637).
REM Geef J als eerste argument mee om toch alleen het eindjaar te rekenen.
set AlleenEindjaar=FALSE

if "%1%" neq "" goto zichtjarenKeuzeGemaakt
CHOICE /M "Wil je alleen het eindjaar uitrekenen, dus de tussenliggende zichtjaren overslaan?"
if ErrorLevel 2 goto zichtjarenKeuzeGemaakt
set AlleenEindjaar=TRUE
:zichtjarenKeuzeGemaakt
if "%1%" equ "J" set AlleenEindjaar=TRUE
if "%1%" equ "N" set AlleenEindjaar=FALSE

if "%2%" equ ""  CHOICE /M "Wil je eerder gemaakte Basedata hergebruiken en dus draaien van PrepareBasedata overslaan?"
if ErrorLevel 2 goto runPrepareBasedata
if "%2%" equ "N" goto runPrepareBasedata

if "%3%" equ ""  CHOICE /M "Wil je eerder gemaakte VariantData hergebruiken en dus het (her)genereren hiervan overslaan?"
if ErrorLevel 2 goto runPrepareVariantdata
if "%3%" equ "N" goto runPrepareVariantdata
goto runScenarios

:runPrepareBasedata

REM deletes the old BaseData folder
REM rmdir %LocalDataProjDir%\Basedata /s /q 

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /WriteBasedata/Generate_Run1
echo "ErrorLevel is " %ErrorLevel% 
if %ErrorLevel% NEQ 0 goto ErrorEnd

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /WriteBasedata/Generate_Run2
echo "ErrorLevel is " %ErrorLevel% 
if %ErrorLevel% NEQ 0 goto ErrorEnd

REM deze ontkoppelde dat is nodig voor de indicatoren.
REM call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /WriteBasedata/Generate_Run3_IndicatorenData
REM echo "ErrorLevel is " %ErrorLevel% 
REM if %ErrorLevel% NEQ 0 goto ErrorEnd


:runPrepareVariantdata

REM deletes the old VariantData folder.
REM rmdir %LocalDataProjDir%\VariantData /s /q

set RSL_VARIANT_NAME=BAU
call ..\batch\RunVariantData.cmd

REM set RSL_VARIANT_NAME=Intensiveren
REM call ..\batch\RunVariantData.cmd

REM set RSL_VARIANT_NAME=Transformeren
REM call ..\batch\RunVariantData.cmd

:runScenarios

set RSL_SCENARIO_NAME=WLO_Hoog
call ..\batch\RunScenarios.cmd

REM set RSL_SCENARIO_NAME=WLO_Laag
REM call ..\batch\RunScenarios.cmd


echo "Klaar !"
pause
exit



:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause

exit