echo off
REM for /f "tokens=2 delims==." %%I in ('"wmic os get localdatetime /value"') do set "TS=%%I"
REM set "TIMESTAMP=%TS:~0,8%-%TS:~8,6%"


setlocal EnableExtensions
for /f "tokens=1-3 delims=-/ " %%a in ("%date%") do (
  for /f "tokens=1-3 delims=:.," %%h in ("%time: =0%") do (
    rem %%a=dd %%b=mm %%c=yyyy ; %%h=HH %%i=MM %%j=SS
    set "TIMESTAMP=%%c%%b%%a-%%h%%i%%j"
  )
)



echo ================================================================

set lognaam_init=%3
set lognaam=%lognaam_init:/=_%

echo "%ProgramPath%" /Llog/%lognaam%_%timeStamp%.txt %MT_FLAGS% %1 %2
"%ProgramPath%" /Llog/%lognaam%_%timeStamp%.txt %MT_FLAGS% %1 %2
type "log\%lognaam%_%timeStamp%.txt" >> log\log.txt

echo Did the following items complete calculations: %1 %2 ?

if %ErrorLevel% NEQ 0 goto ErrorEnd
echo "No errors found"

exit /B

:ErrorEnd
echo "ErrorLevel is " %ErrorLevel%

if %ErrorLevel% == 3 (
 echo ERROR: Unexpected termination after loading %1 to update %2. 
)
if %ErrorLevel% == 2 (
 echo ERROR: failed to load %1 or caught exception during updating %2. 
)
if %ErrorLevel% == 1 (
 echo ERROR: updating of item %2 in %1 failed.
)
if %ErrorLevel% == -1073741819 (
 echo ERROR: Access Violation. Contact Object Vision for support.
)

echo batch will be aborted after pause because of a detected failure
pause
exit