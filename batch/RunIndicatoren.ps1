<#
.SYNOPSIS
    Draait de indicatorenexport voor een of meer zichtjaren en varianten.

.DESCRIPTION
    Leest de stand uit de tifs die de allocatie heeft weggeschreven, dus dit kan zonder de
    allocatie over te doen. Elk zichtjaar is een eigen aanroep, gestuurd door de
    omgevingsvariabele ExportZichtjaar.

    Toetst per stap zowel de exitcode als het log op regels met [E]. Een ontbrekend
    bronbestand kan namelijk met exit 0 aflopen; zie de skill rs-draaien, trap 1.
#>
[CmdletBinding()]
param(
    [string]   $Exe        = 'C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe',
    [string]   $Cfg        = 'C:\ProjDir\RSopen_NL2120_productie\cfg\main.dms',
    [string]   $LogDir     = 'C:\ProjDir\RSopen_NL2120_productie\batch\log\indicatoren',
    [string]   $Scenario   = 'WLO_hoog',
    [string[]] $Varianten  = @('BAU','BAU2'),
    [string[]] $Zichtjaren = @('Y2120'),

    # Op welke regio-indeling de indicatorentabellen aggregeren. Stuurt
    # ModelParameters/Advanced/IndicatorRegio_ref. Zonder deze parameter viel de
    # configuratie stil terug op NL, en dan komen alle tabellen landsdekkend uit
    # terwijl je per landschap wilde leveren. De landelijke tabel komt sinds #705
    # hoe dan ook mee, dus 'Landschap' levert beide en hoeft niet apart nog eens
    # op 'NL' gedraaid te worden.
    [ValidateSet('NL','Provincie','COROP','Gemeente','NVM','Landschap',
                 'Landschap_Kust','Landschap_Rivieren','Landschap_Veen','Landschap_Zand')]
    [string]   $IndicatorRegio = 'NL'
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Exe)) { throw "GeoDmsRun niet gevonden: $Exe" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

$env:StandAllocatieOntkoppeld = 'TRUE'
$env:VariantDataOntkoppeld    = 'TRUE'
$env:AlleenEindjaar           = 'FALSE'
$env:IndicatorRegio           = $IndicatorRegio
Remove-Item Env:\LocalDataProjDir -ErrorAction SilentlyContinue

$status = Join-Path $LogDir 'status.tsv'
if (-not (Test-Path $status)) { "tijd`tstap`texit`tseconden" | Set-Content $status -Encoding UTF8 }

function Write-Regel([string]$T) { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $T" }

$totaal = [Diagnostics.Stopwatch]::StartNew()
Write-Regel "varianten : $($Varianten -join ', ')"
Write-Regel "zichtjaren: $($Zichtjaren -join ', ')"
Write-Regel "regio     : $IndicatorRegio (de landelijke tabel komt hoe dan ook mee, #705)"

foreach ($v in $Varianten) {
    foreach ($y in $Zichtjaren) {
        $stap  = "indicatoren-$v-$y"
        $env:ExportZichtjaar = $y
        $log   = Join-Path $LogDir ("{0}_{1}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'), $stap)
        $item  = "/Indicatoren/${Scenario}_$v/Zichtjaren/Export/Generate_Indicatoren"

        Write-Regel "start     : $stap"
        $sw = [Diagnostics.Stopwatch]::StartNew()
        & $Exe "/L$log" '/S1' '/S2' '/S3' $Cfg $item 2>&1 | Out-Null
        $code = $LASTEXITCODE
        $sw.Stop()
        $sec = [math]::Round($sw.Elapsed.TotalSeconds, 1)

        "{0}`t{1}`t{2}`t{3}" -f (Get-Date -Format 's'), $stap, $code, $sec |
            Add-Content $status -Encoding UTF8

        $fouten = @(Select-String -Path $log -Pattern '\[E\]' -ErrorAction SilentlyContinue)
        if ($code -ne 0 -or $fouten.Count -gt 0) {
            $reden = if ($code -ne 0) { "exit $code" } else { "exit 0 maar $($fouten.Count) foutregels in het log" }
            Write-Regel "MISLUKT   : $stap ($reden, $sec s)"
            $fouten | Select-Object -First 15 | ForEach-Object { Write-Host "   $($_.Line)" }
            throw "Stap '$stap' mislukt: $reden"
        }
        Write-Regel "klaar     : $stap ($([math]::Round($sec/60,1)) min)"
    }
}

$totaal.Stop()
Write-Regel "ALLE INDICATOREN KLAAR in $([math]::Round($totaal.Elapsed.TotalHours,2)) uur"
