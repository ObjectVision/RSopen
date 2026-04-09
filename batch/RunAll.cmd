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
REM Dit script start een volledige RSopen modelrun. Het stelt de benodigde parameters in (paden, GeoDMS versie), vraagt de gebruiker of basedata hergebruikt kan worden en of alleen het eindjaar berekend moet worden, en roept daarna de deelscripts aan.
REM
REM ================================================================================


REM ========== PARAMETER INSTELLINGEN ================
set geodmsversion=GeoDms19.1.0
REM set exe_dir=C:\Program Files\ObjectVision\%geodmsversion%
set exe_dir=C:\dev\GeoDms_2026\bin\Release\x64
set ProgramPath=%exe_dir%\GeoDmsRun.exe
REM set LocalDataProjDir=K:\LD\RSOpen
set LocalDataProjDir=C:\LocalData\RSopen

set MT_FLAGS=/S1 /S2 /S3

set CurrentDir=%CD%
CD ..
set ProjDir=%CD%
CD %CurrentDir%
REM ========= EINDE PARAMETER INSTELLINGEN ===========

REM deletes the old log file; each run adds the timed version to it.
del log\log.txt

set AlleenEindjaar=TRUE

if "%1%" equ "" CHOICE /M "Wil je alleen eindjaar uitrekenen, dus 2030 en 2040 overslaan?"
if ErrorLevel 2 set AlleenEindjaar=FALSE
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