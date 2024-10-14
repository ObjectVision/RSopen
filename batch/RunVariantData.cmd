call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Suitability_Opbrengsten_perOP
REM call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Zeef_AdminDomain_All
REM if %ErrorLevel% NEQ 0 goto ErrorEnd
REM call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Opbrengsten_perOP
REM if %ErrorLevel% NEQ 0 goto ErrorEnd
REM call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Zeef_Domain_All
REM if %ErrorLevel% NEQ 0 goto ErrorEnd
REM call ..\batch\RunImpl.cmd ..\cfg\main.dms /WriteVariantData/Verblijfsrecreatie
REM if %ErrorLevel% NEQ 0 goto ErrorEnd

REM :ErrorEnd
REM echo "%ErrorLevel%"
REM pause "Er gaat iets mis..."