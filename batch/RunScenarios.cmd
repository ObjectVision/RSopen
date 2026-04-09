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
REM Dit script roept per scenario (bijv. BAU, Intensiveren) het RunZichtjaren.cmd script aan om de allocatie voor alle zichtjaren te draaien.
REM
REM ================================================================================

set RSL_VARIANT_NAME=BAU
call ..\batch\RunZichtjaren.cmd

REM set RSL_VARIANT_NAME=Intensiveren
REM call ..\batch\RunZichtjaren.cmd

REM set RSL_VARIANT_NAME=Transformeren
REM call ..\batch\RunZichtjaren.cmd

