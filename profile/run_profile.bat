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
REM Dit script installeert de benodigde Python-packages (psutil, bokeh) en start vervolgens het GeoDMSPerformance.py profilerings-script.
REM
REM ================================================================================

pip install psutil bokeh

python GeoDMSPerformance.py profile_setups.txt
echo oke?
pause