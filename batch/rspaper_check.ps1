# Quick checks for the RS_paper working copy: runs GeoDmsRun on a list of items and reports exit code, time and [E] lines.
param(
    [string[]] $Items,
    [string]   $Tag = 'check'
)
$exe = 'C:\Program Files\ObjectVision\GeoDms20.20.0.m\GeoDmsRun.exe'
$cfg = 'C:\ProjDir\RSopen_RSpaper\cfg\main.dms'
$logdir = 'C:\ProjDir\RSopen_RSpaper\batch\log\rspaper'
New-Item -ItemType Directory -Force -Path $logdir | Out-Null
$log = Join-Path $logdir ("{0}_{1}.log" -f $Tag, (Get-Date -Format 'HHmmss'))
$env:LocalDataProjDir = $null
$env:StandAllocatieOntkoppeld = 'TRUE'
$env:VariantDataOntkoppeld = 'TRUE'
$sw = [Diagnostics.Stopwatch]::StartNew()
& $exe "/L$log" '/S1' '/S2' '/S3' $cfg @Items 2>&1 | Out-Null
$code = $LASTEXITCODE
"exit=$code  secs=$([int]$sw.Elapsed.TotalSeconds)  log=$log"
$err = Select-String -Path $log -Pattern '\[E\]' | Select-Object -First 25
foreach ($e in $err) { $l = $e.Line; $l.Substring(0, [Math]::Min(300, $l.Length)) }
