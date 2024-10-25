call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Zeef_AdminDomain_All
if %ErrorLevel% NEQ 0 goto ErrorEnd
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Opbrengsten_perOP
if %ErrorLevel% NEQ 0 goto ErrorEnd
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Zeef_Domain_All
if %ErrorLevel% NEQ 0 goto ErrorEnd
call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Verblijfsrecreatie
if %ErrorLevel% NEQ 0 goto ErrorEnd

exit /B

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause

exit