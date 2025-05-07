echo off
for /f "tokens=2 delims==." %%I in ('"wmic os get localdatetime /value"') do set "TS=%%I"
set "TIMESTAMP=%TS:~0,8%-%TS:~8,6%"

echo ================================================================

echo "%ProgramPath%" /Llog/log_%timeStamp%.txt %MT_FLAGS% %1 %2
"%ProgramPath%" /Llog/log_%timeStamp%.txt %MT_FLAGS% %1 %2
type "log\log_%timeStamp%.txt" >> log\log.txt

echo Completed %1 %2 ?

if not errorlevel 1 ( exit /b )

if errorlevel 3 (
 echo ERROR: Unexpected termination after loading %1 to update %2. 
)
if %ERRORLEVEL% == 2 (
 echo ERROR: failed to load %1 or caught exception during updating %2. 
)
if %ERRORLEVEL% == 1 (
 echo ERROR: updating of item %2 in %1 failed.
)

echo batch will be aborted after pause because of a detected failure
pause
exit