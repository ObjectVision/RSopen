
REM ========== PARAMETER INSTELLINGEN ================
set geodmsversion=GeoDms17.4.6
set exe_dir=C:\Program Files\ObjectVision\%geodmsversion%
REM set exe_dir=C:\dev\GeoDms\bin\Release\x64
set ProgramPath=%exe_dir%\GeoDmsRun.exe
REM set LocalDataProjDir=K:\LD\RSOpen
set LocalDataProjDir=C:\LocalData\RSopen

set MT_FLAGS=/S1 /S2 /S3

set CurrentDir=%CD%
CD ..
set ProjDir=%CD%
CD %CurrentDir%
REM ========= EINDE PARAMETER INSTELLINGEN ===========


set AlleenEindjaar=TRUE

CHOICE /M "Wil je alleen eindjaar uitrekenen, dus 2030, 2040 en 2050 overslaan?"
if ErrorLevel 2 set AlleenEindjaar=FALSE
CHOICE /M "Wil je eerder gemaakte Basedata hergebruiken en dus draaien van PrepareBasedata overslaan?"
if ErrorLevel 2 goto runPrepareBasedata
CHOICE /M "Wil je eerder gemaakte VariantData hergebruiken en dus het (her)genereren hiervan overslaan?"
if ErrorLevel 2 goto runPrepareVariantdata
goto runScenarios

:runPrepareBasedata

REM deletes the old BaseData folder
rmdir %LocalDataProjDir%\Basedata /s /q 

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /WriteBasedata/Generate_Run1
echo "ErrorLevel is " %ErrorLevel% 
if %ErrorLevel% NEQ 0 goto ErrorEnd

:runPrepareVariantdata

REM deletes the old VariantData folder.
rmdir %LocalDataProjDir%\VariantData /s /q 

REM set RSL_VARIANT_NAME=MO
REM call ..\batch\RunVariantData.cmd

REM set RSL_VARIANT_NAME=RG
REM call ..\batch\RunVariantData.cmd

REM set RSL_VARIANT_NAME=SW
REM call ..\batch\RunVariantData.cmd

REM set RSL_VARIANT_NAME=GL
REM call ..\batch\RunVariantData.cmd

set RSL_VARIANT_NAME=BAU
call ..\batch\RunVariantData.cmd

:runScenarios

set RSL_SCENARIO_NAME=WLO_Hoog
call ..\batch\RunScenarios.cmd

REM set RSL_SCENARIO_NAME=WLO_Laag
REM call ..\batch\RunScenarios.cmd


echo "Klaar ?"
pause

exit



:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause

exit