call ..\batch\RunImpl.cmd %ProjDir%\cfg\main.dms /WriteVariantData/Generate_Run1
if %ErrorLevel% NEQ 0 goto ErrorEnd

exit /B

:ErrorEnd
echo "%ErrorLevel%"
echo "Er gaat iets mis..."
pause

exit