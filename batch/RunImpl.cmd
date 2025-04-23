echo off

for /f "tokens=1-8 delims=.:/-, " %%i in ('echo exit^|cmd /q /k"prompt $D $T"') do (
   for /f "tokens=2-4 skip=1 delims=/-,()" %%a in ('echo.^|date') do (
set dow=%%i
set %%a=%%j
set %%b=%%k
set %%c=%%l
set hh=%%m
set min=%%n
set sec=%%o
set hsec=%%p
)
)
set timeStamp=%yy%%mm%%dd%_%hh%%min%%sec%

echo ================================================================

echo "%ProgramPath%" /Llog/log_%timeStamp%.txt %MT_FLAGS% %1 %2
"%ProgramPath%" /Llog/log_%timeStamp%.txt %MT_FLAGS% %1 %2

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