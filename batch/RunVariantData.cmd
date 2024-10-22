call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Generate_Run1
if %ErrorLevel% NEQ 0 goto ErrorEnd

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause 