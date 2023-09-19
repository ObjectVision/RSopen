if "%AlleenEindjaar%" EQU "TRUE" goto runLastYear

call ..\batch\RunImpl.cmd ..\cfg\main.dms /Analysis/Allocatie/Zichtjaren/Y2030/Impl/Generate
call ..\batch\RunImpl.cmd ..\cfg\main.dms /Analysis/Allocatie/Zichtjaren/Y2040/Impl/Generate

:runLastYear

call ..\batch\RunImpl.cmd ..\cfg\main.dms /Analysis/Allocatie/Zichtjaren/Y2050/Impl/Generate