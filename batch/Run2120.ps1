<#
.SYNOPSIS
    Productierun RSopen NL2120 tot en met zichtjaar 2120, varianten BAU en BAU2.

.DESCRIPTION
    Draait met StandAllocatieOntkoppeld=TRUE, dus elk zichtjaar krijgt een eigen
    GeoDmsRun-proces en leest de stand van het vorige jaar terug uit de tif. Daarmee
    blijft het geheugengebruik per proces beperkt en is de run herstartbaar.

    Zet bewust GEEN LocalDataProjDir: dan leidt GeoDMS die af uit LocalDataDir plus de
    configuratienaam, oftewel C:\LocalData\RSopen_NL2120_productie. RunAll.cmd zet die
    variabele wel, op C:\LocalData\RSopen, en dat is voor deze werkkopie het verkeerde pad.

    Elke stap schrijft een eigen log en een regel in status.tsv. Bij de eerste stap die
    niet met exit 0 eindigt stopt het script.
#>
[CmdletBinding()]
param(
    [string]   $Exe        = 'C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe',
    [string]   $Cfg        = 'C:\ProjDir\RSopen_NL2120_productie\cfg\main.dms',
    [string]   $LocalData  = 'C:\LocalData\RSopen_NL2120_productie',
    [string]   $LogDir     = 'C:\ProjDir\RSopen_NL2120_productie\batch\log\run2120',
    [string]   $Scenario   = 'WLO_hoog',
    [string[]] $Varianten  = @('BAU','BAU2'),
    # Leeg laten: dan haalt het script de zichtjaren uit de configuratie zelf, zodat de lijst hier nooit
    # uit de pas kan lopen met Model_FirstZichtjaar en Model_FinalYear.
    [string[]] $Zichtjaren = @(),
    [switch]   $SkipBasedata,
    [switch]   $SkipVariantData,
    [string]   $StartBij   = '',
    [switch]   $HerbouwBasedata
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Exe)) { throw "GeoDmsRun niet gevonden: $Exe" }
if (-not (Test-Path $Cfg)) { throw "Configuratie niet gevonden: $Cfg" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

# Batchinstellingen. Deze overrulen de defaults in ModelParameters.dms.
$env:StandAllocatieOntkoppeld = 'TRUE'
$env:VariantDataOntkoppeld    = 'TRUE'
$env:AlleenEindjaar           = 'FALSE'
# Nadrukkelijk niet zetten, zie de toelichting hierboven.
Remove-Item Env:\LocalDataProjDir -ErrorAction SilentlyContinue

$status = Join-Path $LogDir 'status.tsv'
if (-not (Test-Path $status)) {
    "tijd`tstap`titem`texit`tseconden" | Set-Content $status -Encoding UTF8
}

$script:Overgeslagen = ($StartBij -ne '')

function Write-Regel([string]$Tekst) {
    $t = (Get-Date -Format 'HH:mm:ss')
    Write-Host "[$t] $Tekst"
}

function Invoke-Stap {
    param([string]$Stap, [string]$Item)

    if ($script:Overgeslagen) {
        if ($Stap -eq $StartBij) { $script:Overgeslagen = $false }
        else { Write-Regel "overslaan : $Stap"; return }
    }

    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $safe  = ($Stap -replace '[\\/:*?"<>|]', '_')
    $log   = Join-Path $LogDir "$stamp`_$safe.log"

    Write-Regel "start     : $Stap"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $Exe "/L$log" '/S1' '/S2' '/S3' $Cfg $Item 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $sw.Stop()
    $sec = [math]::Round($sw.Elapsed.TotalSeconds, 1)

    "{0}`t{1}`t{2}`t{3}`t{4}" -f (Get-Date -Format 's'), $Stap, $Item, $code, $sec |
        Add-Content $status -Encoding UTF8

    # Exit 0 is niet genoeg. Een ontbrekend bronbestand komt als GDAL-fout in het log terwijl de exitcode
    # 0 blijft; gemeten op 2026-08-27 met een claim-CSV die niet bestond. Daarom ook het log toetsen.
    $fouten = @(Select-String -Path $log -Pattern '\[E\]' -ErrorAction SilentlyContinue)

    if ($code -ne 0 -or $fouten.Count -gt 0) {
        $reden = if ($code -ne 0) { "exit $code" } else { "exit 0 maar $($fouten.Count) foutregels in het log" }
        Write-Regel "MISLUKT   : $Stap ($reden, $sec s)"
        Write-Regel "log       : $log"
        $fouten | Select-Object -First 20 | ForEach-Object { Write-Host "   $($_.Line)" }
        throw "Stap '$Stap' mislukt: $reden"
    }

    Write-Regel "klaar     : $Stap ($([math]::Round($sec/60,1)) min)"
}

function Get-Zichtjaren {
    # Haalt de zichtjaren uit de configuratie in plaats van ze hier te herhalen. Zie de memory-notitie
    # over RunZichtjaren.cmd, dat jaartallen bij naam noemde en daardoor stil een zichtjaar oversloeg.
    $log = Join-Path $LogDir 'zichtjaren.log'
    $uit = & $Exe "/L$log" $Cfg '@statistics' '/Classifications/Time/Zichtjaar/YearRange_rel' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Kon de zichtjaren niet uit de configuratie lezen, zie $log" }

    $blok  = (($uit -join "`n") -split 'clipboard:')[-1]
    $jaren = @()
    foreach ($regel in ($blok -split "`n")) {
        if ($regel -match '^\s*([\d.,]+)\s') {
            $j = $matches[1] -replace '[^\d]', ''
            if ($j.Length -eq 4) { $jaren += "Y$j" }
        }
    }
    $jaren = $jaren | Select-Object -Unique
    if ($jaren.Count -eq 0) { throw "Geen zichtjaren gevonden in de configuratie" }
    return $jaren
}

function Test-Dictionaries {
    # Zie de memory mmd-dictionary-relatief-pad: een verse mmd kan een relatief pad in de
    # IntegrityCheck krijgen, waardoor hij bij het teruglezen onvindbaar is.
    $stuk = Get-ChildItem $LocalData -Recurse -Filter '0Dictionary.dms' -ErrorAction SilentlyContinue |
        Where-Object { (Get-Content $_.FullName -Raw) -match '\.\./' }
    if ($stuk) {
        Write-Regel "LET OP: 0Dictionary met relatief pad gevonden, run gestopt:"
        $stuk | ForEach-Object { Write-Host "   $($_.FullName)" }
        throw 'Relatieve paden in 0Dictionary.dms, eerst patchen'
    }
    Write-Regel "controle  : alle 0Dictionary.dms staan absoluut"
}

Write-Regel "build     : $(Split-Path (Split-Path $Exe -Parent) -Leaf)"
Write-Regel "config    : $Cfg"
Write-Regel "localdata : $LocalData"
Write-Regel "varianten : $($Varianten -join ', ')"

if ($Zichtjaren.Count -eq 0) { $Zichtjaren = Get-Zichtjaren }
Write-Regel "zichtjaren: $($Zichtjaren -join ', ') (uit de configuratie)"
Write-Regel "stand ontkoppeld: TRUE, dus een proces per zichtjaar"

$totaal = [Diagnostics.Stopwatch]::StartNew()

function Test-ReeksNogNietBegonnen {
    # Verse basedata of variantdata halverwege een reeks zichtjaren laat de vroege en de late
    # zichtjaren met verschillende invoer rekenen. Het ontkoppelde
    # Verwervingskosten_Woningen_AdminDomain heeft geen fingerprint, dus daar waarschuwt niets voor.
    # Ververs die bestanden dus tussen twee complete reeksen door, nooit ertussenin.
    param([string]$Waarom)

    if ($script:Overgeslagen) { return }   # we zitten nog in de -StartBij-aanloop, deze stap draait toch niet

    $standen = @()
    foreach ($v in $Varianten) {
        $d = Join-Path $LocalData "Allocatie\${Scenario}_$v"
        if (Test-Path $d) {
            Get-ChildItem $d -Directory -Filter 'Stand*' -ErrorAction SilentlyContinue |
                ForEach-Object { $standen += "${Scenario}_$v/$($_.Name)" }
        }
    }

    if ($standen.Count -gt 0 -and -not $HerbouwBasedata) {
        Write-Regel "GESTOPT: $Waarom terwijl er al standen van deze reeks staan:"
        $standen | ForEach-Object { Write-Host "   $_" }
        Write-Regel "Hervat met -StartBij <stap>, of geef -HerbouwBasedata mee als je de reeks bewust opnieuw begint."
        throw "$Waarom geweigerd: er staan al standen van deze reeks"
    }
}

if (-not $SkipBasedata) {
    Test-ReeksNogNietBegonnen 'basedata opnieuw wegschrijven'
    Invoke-Stap 'basedata-run1' '/WriteBasedata/Generate_Run1'
    Invoke-Stap 'basedata-run2' '/WriteBasedata/Generate_Run2'
    Test-Dictionaries
}

if (-not $SkipVariantData) {
    Test-ReeksNogNietBegonnen 'variantdata opnieuw wegschrijven'
    foreach ($v in $Varianten) {
        Invoke-Stap "variantdata-$v-run1" "/WriteVariantData/per_Variant/$v/Generate_Run1"
        Invoke-Stap "variantdata-$v-run2" "/WriteVariantData/per_Variant/$v/Generate_Run2"
    }
}

foreach ($v in $Varianten) {
    foreach ($y in $Zichtjaren) {
        Invoke-Stap "allocatie-$v-$y" "/Allocatie/${Scenario}_$v/Zichtjaren/$y/Impl/Generate"
    }
}

$totaal.Stop()
Write-Regel "ALLES KLAAR in $([math]::Round($totaal.Elapsed.TotalHours,2)) uur"
