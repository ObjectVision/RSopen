
REM ========== PARAMETER INSTELLINGEN ================
set geodmsversion=GeoDms14.1.0
set exe_dir=C:\Program Files\ObjectVision\%geodmsversion%
set ProgramPath=%exe_dir%\GeoDmsRun.exe
set LocalDataProjDir=K:\LD\RSOpen
set MT_FLAGS=/S1 /S2 /S3
REM ========= EINDE PARAMETER INSTELLINGEN ===========


set AlleenEindjaar=TRUE

CHOICE /M "Wil je alleen eindjaar uitrekenen, dus 2030 en 2040 overslaan?"
if ErrorLevel 2 set AlleenEindjaar=FALSE
CHOICE /M "Wil je eerder gemaakte Basedata hergebruiken en dus draaien van PrepareBasedata overslaan?"
if ErrorLevel 2 goto runPrepareBasedata
CHOICE /M "Wil je eerder gemaakte VariantData hergebruiken en dus het (her)genereren hiervan overslaan?"
if ErrorLevel 2 goto runPrepareVariantdata
goto runScenarios

:runPrepareBasedata

REM rmdir %LocalDataProjDir%\Basedata /s /q REM deletes the old BaseData folder

call ..\batch\RunImpl.cmd ..\cfg\main.dms /Geography/RegioIndelingen/Impl/Generate_Run1
call ..\batch\RunImpl.cmd ..\cfg\main.dms /Geography/RegioIndelingen/Impl/Generate_Run2

call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run1
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run2
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run3
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run4
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run5
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run6
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run7
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run8
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run9
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteBasedata/Generate_Run10

:runPrepareVariantdata

rmdir %LocalDataProjDir%\VariantData /s /q REM deletes the old VariantData folder.

set RSL_VARIANT_NAME=MO
call ..\batch\RunVariantData.cmd

set RSL_VARIANT_NAME=RG
call ..\batch\RunVariantData.cmd

set RSL_VARIANT_NAME=SW
call ..\batch\RunVariantData.cmd

set RSL_VARIANT_NAME=GL
call ..\batch\RunVariantData.cmd

set RSL_VARIANT_NAME=BAU
call ..\batch\RunVariantData.cmd

:runScenarios

set RSL_SCENARIO_NAME=WLO_Hoog
call ..\batch\RunScenarios.cmd

set RSL_SCENARIO_NAME=WLO_Laag
call ..\batch\RunScenarios.cmd

pause "Klaar ?"