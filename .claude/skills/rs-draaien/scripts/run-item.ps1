<#
.SYNOPSIS
    Rekent een item uit de RSopen-config door met GeoDmsRun en meldt de uitkomst.

.DESCRIPTION
    Kiest de nieuwste geinstalleerde GeoDMS-build (of de opgegeven versie), draait het
    item, meet de rekentijd en toont de [E]-regels uit het log. De rekentijd staat er
    bewust bij: exit 0 in enkele milliseconden op een groot attribuut betekent dat alleen
    de metadata is gecontroleerd en niet dat er gerekend is.

.EXAMPLE
    .\run-item.ps1 -Item "/Indicatoren/WLO_hoog_BAU/Zichtjaren/Y2030/Stand/Aantal_Woningen_Totaal"

.EXAMPLE
    .\run-item.ps1 -Item "/CommitChecks/MaakBaseData1" -Version "20.16.0.m" -ShowLog
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Item,

    [string]$Config = "C:\ProjDir\RSopen_NL2120\cfg\main.dms",

    # Bijvoorbeeld "20.17.0.m". Leeg = nieuwste geinstalleerde .m-build.
    [string]$Version = "",

    [string]$LogDir = "$env:TEMP\rsopen-check",

    # Toon het volledige log in plaats van alleen de foutregels.
    [switch]$ShowLog,

    # Laat GeoDmsRun live naar het scherm schrijven (handig bij lange runs).
    [switch]$Stream
)

$ErrorActionPreference = "Stop"

$ovRoot = "C:\Program Files\ObjectVision"

if ($Version) {
    $exe = Join-Path $ovRoot "GeoDms$Version\GeoDmsRun.exe"
    if (-not (Test-Path $exe)) { throw "GeoDmsRun niet gevonden: $exe" }
} else {
    $builds = Get-ChildItem $ovRoot -Directory -Filter "GeoDms*.m" |
        Sort-Object { [version](($_.Name -replace '^GeoDms', '') -replace '\.m$', '') }
    if (-not $builds) { throw "Geen GeoDms*.m build gevonden onder $ovRoot" }
    $exe = Join-Path $builds[-1].FullName "GeoDmsRun.exe"
}

if (-not (Test-Path $Config)) { throw "Config niet gevonden: $Config" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$safe  = ($Item -replace '[\/:*?"<>|]', '_').Trim('_')
if ($safe.Length -gt 60) { $safe = $safe.Substring($safe.Length - 60) }
$log   = Join-Path $LogDir "$stamp`_$safe.log"

Write-Host "build : $(Split-Path $exe -Parent | Split-Path -Leaf)"
Write-Host "config: $Config"
Write-Host "item  : $Item"
Write-Host "log   : $log"
Write-Host ""

$sw = [System.Diagnostics.Stopwatch]::StartNew()
if ($Stream) {
    & $exe "/L$log" $Config $Item
} else {
    # GeoDmsRun echoot het volledige log naar stdout; dat onderdrukken we, want
    # het log wordt hieronder toch gelezen.
    & $exe "/L$log" $Config $Item 2>&1 | Out-Null
}
$code = $LASTEXITCODE
$sw.Stop()

$secs = [math]::Round($sw.Elapsed.TotalSeconds, 3)

$verdict = switch ($code) {
    0       { "OK" }
    1       { "REKENFOUT of gefaalde IntegrityCheck" }
    2       { "PARSE- of LAADFOUT" }
    default { "onbekende exitcode" }
}

Write-Host ""
Write-Host "exitcode $code ($verdict) in $secs s"

if (Test-Path $log) {
    if ($ShowLog) {
        Get-Content $log
    } else {
        $errs = Select-String -Path $log -Pattern '\[E\]' -SimpleMatch:$false
        if ($errs) {
            Write-Host ""
            Write-Host "foutregels uit het log:"
            $errs | Select-Object -First 40 | ForEach-Object { Write-Host "  $($_.Line)" }
            if ($errs.Count -gt 40) { Write-Host "  ... en nog $($errs.Count - 40) regels" }
        }
    }
}

if ($code -eq 0 -and $secs -lt 0.5) {
    Write-Host ""
    Write-Host "Let op: in $secs s klaar. Dit bewijst parse, naamresolutie en domeincheck," -ForegroundColor Yellow
    Write-Host "maar waarschijnlijk niet dat de data is doorgerekend. Forceer het rekenen met" -ForegroundColor Yellow
    Write-Host "een aggregerende parameter of een IntegrityCheck op de data." -ForegroundColor Yellow
}

exit $code
