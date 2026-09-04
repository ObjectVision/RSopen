<#
.SYNOPSIS
    Draait de indicatorenexport voor een of meer zichtjaren en varianten.

.DESCRIPTION
    Leest de stand uit de tifs die de allocatie heeft weggeschreven, dus dit kan zonder de
    allocatie over te doen. Elk zichtjaar is een eigen aanroep, gestuurd door de
    omgevingsvariabele ExportZichtjaar.

    Standaard is dat een proces per variant en zichtjaar. Met -Gebundeld gaan per zichtjaar
    alle varianten als losse itempaden in een GeoDmsRun-aanroep: de engine werkt ze dan na
    elkaar af in hetzelfde proces, zodat wat de casussen delen (SourceData, BaseData, de
    regio-indelingen, de dieptekaarten) maar een keer hoeft te worden ingelezen. Dat is op
    4 september 2026 bewezen te werken op 20.17.0.m: elk item krijgt zijn eigen Updating-paar
    in het log, en een item dat faalt geeft exit 1 zonder de andere te raken. Hoeveel het
    scheelt is nog niet gemeten, en een gebundeld proces houdt meer tegelijk vast; daarom is
    het een schakelaar en niet de standaard. Bewust niet via een verzamelitem met
    ExplicitSuppliers in de configuratie, want dat zou ook NbSMax meetrekken en laat de drie
    exports gelijktijdig naar de ene gedeelde basisjaartif schrijven (#773).

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
    [string]   $IndicatorRegio = 'NL',

    # Per zichtjaar een proces voor alle varianten samen, zie .DESCRIPTION. De rekentijd per
    # casus komt dan uit de Updating-regels in het log en niet uit de stopwatch.
    [switch]   $Gebundeld
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

function Invoke-Export([string]$stap, [string[]]$items) {
    $log = Join-Path $LogDir ("{0}_{1}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'), $stap)

    Write-Regel "start     : $stap"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $Exe "/L$log" '/S1' '/S2' '/S3' $Cfg @items 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $sw.Stop()
    $sec = [math]::Round($sw.Elapsed.TotalSeconds, 1)

    "{0}`t{1}`t{2}`t{3}" -f (Get-Date -Format 's'), $stap, $code, $sec |
        Add-Content $status -Encoding UTF8

    # Gebundeld geeft GeoDmsRun een exitcode voor alle casussen samen. De rekentijd per casus
    # staat wel in het log: elk opdrachtregelitem krijgt zijn eigen Updating-paar. Die komt
    # als eigen regel in status.tsv, zodat de tijd per variant vergelijkbaar blijft met de
    # losse aanroepen.
    if ($items.Count -gt 1) {
        Select-String -Path $log -Pattern '\} Updating::\[\[/Indicatoren/([^/]+)/.*\]\] \(([\d.,]+) secs\)' -ErrorAction SilentlyContinue |
            ForEach-Object {
                $casus = $_.Matches[0].Groups[1].Value
                $csec  = [double]($_.Matches[0].Groups[2].Value -replace ',', '.')
                "{0}`t{1}`t{2}`t{3}" -f (Get-Date -Format 's'), "$stap ($casus)", $code, [math]::Round($csec, 1) |
                    Add-Content $status -Encoding UTF8
                Write-Regel "  casus   : $casus ($([math]::Round($csec/60,1)) min)"
            }
    }

    $fouten = @(Select-String -Path $log -Pattern '\[E\]' -ErrorAction SilentlyContinue)
    if ($code -ne 0 -or $fouten.Count -gt 0) {
        $reden = if ($code -ne 0) { "exit $code" } else { "exit 0 maar $($fouten.Count) foutregels in het log" }
        Write-Regel "MISLUKT   : $stap ($reden, $sec s)"
        $fouten | Select-Object -First 15 | ForEach-Object { Write-Host "   $($_.Line)" }
        throw "Stap '$stap' mislukt: $reden"
    }
    Write-Regel "klaar     : $stap ($([math]::Round($sec/60,1)) min)"
}

if ($Gebundeld) {
    Write-Regel "modus     : gebundeld, per zichtjaar een proces voor $($Varianten.Count) varianten"
    foreach ($y in $Zichtjaren) {
        $env:ExportZichtjaar = $y
        $items = @($Varianten | ForEach-Object { "/Indicatoren/${Scenario}_$_/Zichtjaren/Export/Generate_Indicatoren" })
        Invoke-Export "indicatoren-gebundeld-$y" $items
    }
} else {
    foreach ($v in $Varianten) {
        foreach ($y in $Zichtjaren) {
            $env:ExportZichtjaar = $y
            Invoke-Export "indicatoren-$v-$y" @("/Indicatoren/${Scenario}_$v/Zichtjaren/Export/Generate_Indicatoren")
        }
    }
}

$totaal.Stop()
Write-Regel "ALLE INDICATOREN KLAAR in $([math]::Round($totaal.Elapsed.TotalHours,2)) uur"
