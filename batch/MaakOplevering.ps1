<#
.SYNOPSIS
    Stelt uit de ruwe indicatorenuitvoer in LocalData een opleveringsmap samen.

.DESCRIPTION
    LocalData blijft ongemoeid: dit script kopieert en hernoemt alleen. De ruwe map is
    plat en draagt namen die het model nodig heeft (studiegebied, aantal subsectoren,
    mapnamen als losse jaartallen). De opleveringsmap is ingedeeld naar wat de ontvanger
    zoekt: tabellen, kaarten van het zichtjaar, de tijdreeks en het basisjaar.

    Elke kaart bestaat uit drie bestanden: de tif, het world file .tfw en een .xml met
    het GeoDMS-itempad en de buildversie. Die xml is herkomst en gaat bewust mee.
#>
[CmdletBinding()]
param(
    [string] $Bron      = 'C:\LocalData\RSopen_NL2120_productie\Indicatoren',
    # Standaard naar de gedeelde projectmap, zodat de levering meteen bij het team staat.
    [string] $Doel      = 'C:\Users\JipClaassens\Objectvision\Object Vision - General\LocalData\RSOpen_NL2120\Productierun_20260829\Indicatoren',
    [string] $Zichtjaar = 'Y2120',
    [string] $Commit    = ''
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Bron)) { throw "Bronmap niet gevonden: $Bron" }
if (Test-Path $Doel) { throw "Doelmap bestaat al, verwijder of hernoem hem eerst: $Doel" }

$varianten = [ordered]@{
    'WLO_hoog_BAU'            = 'BAU1'
    'WLO_hoog_BAU2'           = 'BAU2'
    'WLO_hoog_NbSGenuanceerd' = 'NbSGenuanceerd'
    'WLO_hoog_NbSMax'         = 'NbSMax'
}

function Schoon([string]$Naam) {
    # Haalt de modelstaart uit de naam: _Nederland_SS-11 of _Nederland vlak voor de extensie.
    $kaal = ($Naam -replace '_Nederland_SS-11(?=\.)', '') -replace '_Nederland(?=\.)', ''
    # De landelijke claimtabel heet ClaimRealisatie_Nederland_Nederland_SS-11 en verliest daardoor
    # twee keer een Nederland: eerst het studiegebied, dan het schaalniveau. Wat overblijft leest
    # als de hoofdtabel terwijl het het landelijke totaal is. Geef dat niveau terug.
    if ($kaal.StartsWith("ClaimRealisatie.")) { $kaal = "ClaimRealisatie_NL." + $kaal.Substring(16) }
    return $kaal
}

# Op verzoek van Deltares (#717) blijft de bestaande bereikbaarheid-groen-indicator buiten de
# levering. Die telt de landgebruiksklasse van een hele cel en kent geen groenfractie, waardoor
# het groen binnen ontwikkelpakketten er per constructie onzichtbaar voor is; de indicator
# spreekt het NbS-verhaal daardoor tegen in plaats van het te ondersteunen. Er komt een
# fractiegebaseerde opvolger. De bestanden blijven wel gewoon in LocalData staan.
# Ook de losse per-itemkaarten (naamvorm Bereikbaarheid_Groen_...) vallen onder de uitsluiting;
# op verzoek van Deltares (#717) gaat alleen de niet-druktegecorrigeerde fractiemaat mee.
$NietUitleveren = @('BereikbaarheidGroen', 'Bereikbaarheid_Groen_')
$NietUitleverenKolommen = @(
    'BereikbaarheidGroen_BBG_Tot300m_ExAgr_Groenaanbod_over_woning'
    'BereikbaarheidGroen_BBG_Tot300m_Groenaanbod_over_woning'
    'BereikbaarheidGroen_BBG_Tot300m_ExAgr_DrukteCorr_PerWoning'
    'BereikbaarheidGroen_BBG_Tot300m_DrukteCorr_PerWoning'
    'BereikbaarheidGroen_Fractie_Tot300m_DrukteCorr_PerWoning'
)

# De fractiegebaseerde opvolger heet BereikbaarheidGroen_Fractie en bevat dus de string waarop
# hierboven wordt uitgesloten. Die moet er juist wel in, dus laat alles met _Fractie expliciet door.
$TochUitleveren = @('_Fractie_Cumulatief', 'BereikbaarheidGroen_Fractie.')

function Uitgesloten([string]$Naam) {
    foreach ($t in $TochUitleveren) { if ($Naam -like "*$t*") { return $false } }
    foreach ($p in $NietUitleveren) { if ($Naam -like "*$p*") { return $true } }
    return $false
}

function Kopieer {
    # Kopieert een tif plus zijn .tfw en .xml naar de doelmap, onder een opgeschoonde naam.
    param([System.IO.FileInfo]$Tif, [string]$NaarMap, [string]$Voorvoegsel = '')

    if (Uitgesloten $Tif.Name) { return 0 }

    if (-not (Test-Path $NaarMap)) { New-Item -ItemType Directory -Path $NaarMap -Force | Out-Null }
    $nieuw = $Voorvoegsel + (Schoon $Tif.Name)
    foreach ($ext in '.tif', '.tfw', '.xml') {
        $mee = [IO.Path]::ChangeExtension($Tif.FullName, $ext)
        if (Test-Path $mee) {
            Copy-Item $mee (Join-Path $NaarMap ([IO.Path]::ChangeExtension($nieuw, $ext))) -Force
        }
    }
    return 1
}

New-Item -ItemType Directory -Path $Doel -Force | Out-Null
$telling = [ordered]@{}

foreach ($casus in $varianten.Keys) {
    $v   = $varianten[$casus]
    $src = Join-Path $Bron $casus
    if (-not (Test-Path $src)) { Write-Host "overgeslagen, casus ontbreekt: $casus"; continue }

    $tab  = Join-Path $Doel "$v\tabellen"
    $jaar = Join-Path $Doel "$v\kaarten_$Zichtjaar"
    $reeks= Join-Path $Doel "$v\kaarten_tijdreeks"
    $basis= Join-Path $Doel "$v\kaarten_basisjaar"
    $n = @{ tabellen = 0; zichtjaar = 0; tijdreeks = 0; basisjaar = 0 }

    # tabellen: de csv's plus hun xml, uit de Stand-map
    New-Item -ItemType Directory -Path $tab -Force | Out-Null
    Get-ChildItem "$src\Stand$Zichtjaar" -Filter '*.csv' -ErrorAction SilentlyContinue | ForEach-Object {
        $uit = Join-Path $tab (Schoon $_.Name)
        # RegionaleIndicatoren draagt de uitgesloten kolommen. Die worden hier weggelaten en niet
        # in de configuratie, want dit is een leverkeuze en geen modelwijziging.
        $kop = Get-Content $_.FullName -TotalCount 1
        if ($NietUitleverenKolommen | Where-Object { $kop -like "*$_*" }) {
            Import-Csv $_.FullName | Select-Object -Property * -ExcludeProperty $NietUitleverenKolommen |
                Export-Csv $uit -NoTypeInformation -Encoding UTF8
        } else {
            Copy-Item $_.FullName $uit -Force
        }
        $x = [IO.Path]::ChangeExtension($_.FullName, '.xml')
        if (Test-Path $x) { Copy-Item $x (Join-Path $tab (Schoon ([IO.Path]::GetFileName($x)))) -Force }
        $n.tabellen++
    }

    # de gpkg met de bereikbaarheid van banen, per buurt en per provincie; die hoort bij de
    # tabellen en niet bij de kaarten, want het is een vectorbestand met attribuuttabellen
    Get-ChildItem $src -File -Filter '*.gpkg' -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $tab (Schoon $_.Name)) -Force
        $n.tabellen++
    }

    # de standgrids van het zichtjaar
    Get-ChildItem "$src\Stand$Zichtjaar" -Filter '*.tif' -ErrorAction SilentlyContinue |
        ForEach-Object { $n.zichtjaar += Kopieer $_ $jaar }

    # de NL2120-landgebruikskaart
    Get-ChildItem "$src\LandgebruikNL2120" -Filter '*.tif' -ErrorAction SilentlyContinue |
        ForEach-Object { $n.zichtjaar += Kopieer $_ $jaar 'LandgebruikskaartNL2120_' }

    # de gewone landgebruikskaart: basisjaar apart, zichtjaar apart, de rest in de reeks
    Get-ChildItem "$src\Landgebruik" -Filter '*.tif' -ErrorAction SilentlyContinue | ForEach-Object {
        if     ($_.Name -match 'Basisjaar')  { $n.basisjaar += Kopieer $_ $basis 'Landgebruikskaart_' }
        elseif ($_.Name -match "^$Zichtjaar"){ $n.zichtjaar += Kopieer $_ $jaar  'Landgebruikskaart_' }
        else                                 { $n.tijdreeks += Kopieer $_ $reeks 'Landgebruikskaart_' }
    }

    # de losse kaarten in de wortel, gesorteerd op het jaartal in de naam
    Get-ChildItem $src -File -Filter '*.tif' | ForEach-Object {
        if     ($_.Name -match "_$Zichtjaar(_|\.)") { $n.zichtjaar += Kopieer $_ $jaar }
        elseif ($_.Name -match '_Y\d{4}(_|\.)')     { $n.tijdreeks += Kopieer $_ $reeks }
        else                                        { $n.basisjaar += Kopieer $_ $basis }
    }

    $telling[$v] = $n
    Write-Host ("{0}: {1} tabellen, {2} kaarten {3}, {4} kaarten tijdreeks, {5} kaarten basisjaar" -f `
        $v, $n.tabellen, $n.zichtjaar, $Zichtjaar, $n.tijdreeks, $n.basisjaar)
}

# de losse casus Basisjaar, zoals hij is
if (Test-Path "$Bron\Basisjaar") {
    Get-ChildItem "$Bron\Basisjaar" -File -Filter '*.tif' |
        ForEach-Object { [void](Kopieer $_ (Join-Path $Doel 'Basisjaar')) }
}

$regels = @()
$regels += "Oplevering RuimteScanner NL2120, issue #658"
$regels += "Samengesteld op $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
$regels += ""
$regels += "Zichtjaar $Zichtjaar, varianten BAU1 en BAU2."
if ($Commit) { $regels += "Configuratie: commit $Commit op branch oplevering-658-20260828." }
$regels += ""
$regels += "INDELING"
$regels += "  <variant>/tabellen/            RegionaleIndicatoren (een regel, heel Nederland), de arealen"
$regels += "                                 per landgebruiksklasse, de claimrealisatie per schaalniveau"
$regels += "                                 en de bereikbaarheid van banen als gpkg"
$regels += "  <variant>/kaarten_$Zichtjaar/       de kaarten van het zichtjaar zelf"
$regels += "  <variant>/kaarten_tijdreeks/   dezelfde indicatoren voor 2040 tot en met 2110, voor"
$regels += "                                 de indicatoren die hun hele reeks wegschrijven"
$regels += "  <variant>/kaarten_basisjaar/   referentiekaarten van het basisjaar"
$regels += "  Basisjaar/                     de losse basisjaarcasus, nu alleen de verhardingskaart"
$regels += ""
$regels += "BESTANDEN"
$regels += "  Elke kaart is een GeoTIFF in RD-coordinaten (EPSG:28992), met een .tfw world file"
$regels += "  en een .xml met het GeoDMS-itempad en de buildversie waarmee hij is gemaakt."
$regels += ""
$regels += "  ClaimRealisatie_<niveau>.csv geeft per regio de gerealiseerde stand gedeeld door de"
$regels += "  claim. Het verschil tussen de niveaus maakt overflow zichtbaar: staat een regio op NVM"
$regels += "  boven de 1 terwijl COROP eromheen op 1 uitkomt, dan is de claim binnen die grotere regio"
$regels += "  verschoven en niet landelijk overschreden."
$regels += ""
$regels += "LET OP BIJ HET LEZEN"
$regels += "  De sloopindicatoren zijn geen tijdreeks. Ze worden geteld uit de stand in het"
$regels += "  basisjaar onder het opleggingsmasker, en dat masker gaat in het eerste zichtjaar in"
$regels += "  een keer op. De waarde is daardoor in elk zichtjaar gelijk."
$regels += "  Vanaf 2060 staat de TIGRIS-claim voor wonen en werken stil; latere zichtjaren"
$regels += "  bouwen alleen nog terug wat de exogene opleggingen slopen."
$regels | Set-Content (Join-Path $Doel 'LEESMIJ.txt') -Encoding UTF8

$totaal = Get-ChildItem $Doel -Recurse -File | Measure-Object Length -Sum
Write-Host ("klaar: {0} bestanden, {1} GB in {2}" -f $totaal.Count, [math]::Round($totaal.Sum/1GB,2), $Doel)
