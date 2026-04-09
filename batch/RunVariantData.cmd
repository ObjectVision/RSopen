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
REM Dit script exporteert de VariantData voor een specifieke variant via GeoDmsRun. Het wordt aangeroepen vanuit RunAll.cmd na de allocatie.
REM
REM ================================================================================

call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /WriteVariantData/per_Variant/%RSL_VARIANT_NAME%/Generate_Run1
if %ErrorLevel% NEQ 0 goto ErrorEnd

exit /B


:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause

exit