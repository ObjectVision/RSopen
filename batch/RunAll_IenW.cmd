
REM ========== PARAMETER INSTELLINGEN ================
set geodmsversion=GeoDms16.0.5
set exe_dir=C:\Program Files\ObjectVision\%geodmsversion%
set ProgramPath=%exe_dir%\GeoDmsRun.exe
REM set LocalDataProjDir=K:\LD\RSOpen
set LocalDataProjDir=C:\LocalData\RSopen_RVFriesland

set CurrentDir=%CD%
CD ..
set ProjDir=%CD%
CD %CurrentDir%

set MT_FLAGS=/S1 /S2 /S3
REM ========= EINDE PARAMETER INSTELLINGEN ===========

set AlleenEindjaar=TRUE
set RSO_VARIANT_NAME=BAU
set RSO_SCENARIO_NAME=WLO_Hoog


REM case(TredesBAUmetLadder  && BouwenNietInGevaarlijk  && NietBouwenWaarSlap , '_mLadder_nGev_nSlap')
REM set RSO_TredesBAUmetLadder=TRUE
REM set RSO_BouwenNietInGevaarlijk=TRUE
REM set RSO_NietBouwenWaarSlap=TRUE
REM call ..\batch\RunVariant_IenW.cmd

REM ,case(TredesBAUmetLadder  && BouwenNietInGevaarlijk  && !NietBouwenWaarSlap, '_mLadder_nGev_wSlap')
REM set RSO_TredesBAUmetLadder=TRUE
REM set RSO_BouwenNietInGevaarlijk=TRUE
REM set RSO_NietBouwenWaarSlap=FALSE
REM call ..\batch\RunVariant_IenW.cmd

REM ,case(TredesBAUmetLadder  && !BouwenNietInGevaarlijk && !NietBouwenWaarSlap, '_mLadder_wGev_wSlap') //bau
REM set RSO_TredesBAUmetLadder=TRUE
REM set RSO_BouwenNietInGevaarlijk=FALSE
REM set RSO_NietBouwenWaarSlap=FALSE
REM call ..\batch\RunVariant_IenW.cmd

REM ,case(TredesBAUmetLadder  && !BouwenNietInGevaarlijk && NietBouwenWaarSlap , '_mLadder_wGev_nSlap')
REM set RSO_TredesBAUmetLadder=TRUE
REM set RSO_BouwenNietInGevaarlijk=FALSE
REM set RSO_NietBouwenWaarSlap=TRUE
REM call ..\batch\RunVariant_IenW.cmd

REM ,case(!TredesBAUmetLadder && !BouwenNietInGevaarlijk && !NietBouwenWaarSlap, '_zLadder_wGev_wSlap')
set RSO_TredesBAUmetLadder=FALSE
set RSO_BouwenNietInGevaarlijk=FALSE
set RSO_NietBouwenWaarSlap=FALSE
call ..\batch\RunVariant_IenW.cmd

REM ,case(!TredesBAUmetLadder && !BouwenNietInGevaarlijk && NietBouwenWaarSlap , '_zLadder_wGev_nSlap')
set RSO_TredesBAUmetLadder=FALSE
set RSO_BouwenNietInGevaarlijk=FALSE
set RSO_NietBouwenWaarSlap=TRUE
call ..\batch\RunVariant_IenW.cmd

REM ,case(!TredesBAUmetLadder && BouwenNietInGevaarlijk  && !NietBouwenWaarSlap, '_zLadder_nGev_wSlap')
set RSO_TredesBAUmetLadder=FALSE
set RSO_BouwenNietInGevaarlijk=TRUE
set RSO_NietBouwenWaarSlap=FALSE
call ..\batch\RunVariant_IenW.cmd

REM ,case(!TredesBAUmetLadder && BouwenNietInGevaarlijk  && NietBouwenWaarSlap , '_zLadder_nGev_nSlap')
set RSO_TredesBAUmetLadder=FALSE
set RSO_BouwenNietInGevaarlijk=TRUE
set RSO_NietBouwenWaarSlap=TRUE
call ..\batch\RunVariant_IenW.cmd


echo "Klaar ?"
pause

exit


:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause

exit