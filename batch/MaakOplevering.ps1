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

    De LEESMIJ wordt aan het eind afgeleid uit wat er werkelijk in de doelmap staat en uit git,
    en niet uit vaste tekst. Zie #731: een LEESMIJ die varianten belooft die er niet zijn, is
    misleidender dan geen LEESMIJ. Wat per levering verandert (issuenummer, verwachte varianten,
    aantekeningen) staat daarom in de parameters hieronder.

.EXAMPLE
    .\MaakOplevering.ps1 -Doel D:\Oplevering\Indicatoren -Issue 632

.EXAMPLE
    Tweede stap van een levering die in delen wordt gevuld. De LEESMIJ wordt opnieuw afgeleid
    uit de dan complete doelmap.

    .\MaakOplevering.ps1 -Doel D:\Oplevering\Indicatoren -Aanvullen
#>
[CmdletBinding()]
param(
    [string] $Bron      = 'C:\LocalData\RSopen_NL2120_productie\Indicatoren',
    # Standaard naar de gedeelde projectmap, zodat de levering meteen bij het team staat.
    [string] $Doel      = 'C:\Users\JipClaassens\Objectvision\Object Vision - General\LocalData\RSOpen_NL2120\Productierun_20260829\Indicatoren',
    [string] $Zichtjaar = 'Y2120',
    # Het issue waaronder deze oplevering valt. Verandert per levering, dus een parameter en geen
    # regel tekst onderin het script.
    [string] $Issue     = '632',
    # De werkkopie die de cijfers heeft gemaakt, en niet de werkkopie waarin dit script staat.
    # Run2120.ps1 draait op RSopen_NL2120_productie terwijl dit script ergens anders kan liggen;
    # die twee kunnen los van elkaar uit de pas lopen. Branch, commit en tag komen hier vandaan.
    [string] $Werkkopie = 'C:\ProjDir\RSopen_NL2120_productie',
    # Vervangt de uit git afgeleide herkomstregels door eigen tekst. Nodig zodra de varianten niet
    # allemaal op dezelfde commit zijn doorgerekend.
    [string[]] $Herkomst = @(),
    # Welke varianten in deze levering horen. Leeg is alle vier uit de tabel hieronder. Wat verwacht
    # wordt maar niet in de doelmap staat, komt met naam in de LEESMIJ en op het scherm.
    [string[]] $Verwacht = @(),
    # Aantekeningen die alleen voor deze levering gelden, bijvoorbeeld op welke servers is gerekend.
    # Wat voor elke oplevering geldt hoort in de vaste tekst onderin dit script, want de LEESMIJ in
    # de doelmap wordt bij elke run overschreven.
    [string[]] $Notitie  = @(),
    # Schrijven in een bestaande doelmap. Nodig als een levering in stappen wordt gevuld; de LEESMIJ
    # wordt dan opnieuw afgeleid uit alles wat er op dat moment staat.
    [switch]   $Aanvullen
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Bron)) { throw "Bronmap niet gevonden: $Bron" }
if ((Test-Path $Doel) -and (-not $Aanvullen)) {
    throw "Doelmap bestaat al. Verwijder of hernoem hem, of gebruik -Aanvullen: $Doel"
}

$varianten = [ordered]@{
    'WLO_hoog_BAU'            = 'BAU1'
    'WLO_hoog_BAU2'           = 'BAU2'
    'WLO_hoog_NbSGenuanceerd' = 'NbSGenuanceerd'
    'WLO_hoog_NbSMax'         = 'NbSMax'
}
if (-not $Verwacht) { $Verwacht = @($varianten.Values) }
$Issue = $Issue.TrimStart('#')

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
#
# Let op de volgorde van de namen. Uitgesloten wordt aangeroepen op de RUWE bestandsnaam, dus voor
# Schoon de modelstaart eraf haalt. Die naam eindigt altijd op _Nederland of _Nederland_SS-11 voor
# de extensie. Een doorlaatpatroon dat op een punt eindigt, zoals 'BereikbaarheidGroen_Fractie.',
# matcht daarom nooit; dat patroon was geschreven voor de opgeschoonde naam en liet in de praktijk
# juist de hoofdkaart van de fractievariant uit de levering vallen. Patronen hier moeten dus tegen
# de ruwe naam gelezen worden.
$TochUitleveren = @('_Fractie_Cumulatief', 'BereikbaarheidGroen_Fractie_', '_Tot300m_Fractie_')

# De druktegecorrigeerde fractiemaat gaat op verzoek van Deltares (#717) niet mee, ook niet als kaart.
# Die staat als kolom al in $NietUitleverenKolommen; deze lijst doet hetzelfde voor de kaarten en gaat
# voor op de doorlaat hierboven, want de bestandsnaam draagt zowel _Fractie_ als de druktecorrectie.
$AltijdUitsluiten = @('_Fractie_Drukte_gecorrigeerd_')

function Uitgesloten([string]$Naam) {
    foreach ($a in $AltijdUitsluiten) { if ($Naam -like "*$a*") { return $true } }
    foreach ($t in $TochUitleveren)   { if ($Naam -like "*$t*") { return $false } }
    foreach ($p in $NietUitleveren)   { if ($Naam -like "*$p*") { return $true } }
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

function Opsomming([string[]]$Delen) {
    # Zodat de LEESMIJ een zin wordt en geen lijstje: a, b en c.
    if ($Delen.Count -le 1) { return ($Delen -join '') }
    return (($Delen[0..($Delen.Count - 2)] -join ', ') + ' en ' + $Delen[-1])
}

function Get-Herkomst([string]$Pad) {
    # Leest branch, commit en tag uit de werkkopie die de cijfers heeft gemaakt. Alles wat hier
    # misgaat levert een regel op die dat zegt; een ontbrekende herkomstregel is niet te
    # onderscheiden van een oplevering waarvan de herkomst wel bekend is.
    if (-not (Test-Path $Pad)) { return @("Configuratie: werkkopie $Pad niet gevonden, herkomst onbekend.") }

    try {
        $branch = git -C $Pad rev-parse --abbrev-ref HEAD 2>$null
        $commit = git -C $Pad rev-parse --short HEAD 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $commit) {
            $global:LASTEXITCODE = 0
            return @("Configuratie: geen git-informatie te lezen uit $Pad.")
        }

        # Faalt met exitcode 128 zodra HEAD niet getagd is. Dat is hier geen fout maar een feit dat in
        # de LEESMIJ hoort, anders leest een ongetagde oplevering als een getagde. De exitcode moet wel
        # opgeruimd worden, want anders eindigt het script erop en leest een aanroeper dat als mislukt.
        $tag = git -C $Pad describe --tags --exact-match 2>$null
        if ($LASTEXITCODE -ne 0) { $tag = '' }
        $vuil = @(git -C $Pad status --porcelain 2>$null)
        $global:LASTEXITCODE = 0
    }
    catch {
        $global:LASTEXITCODE = 0
        return @("Configuratie: git niet aan te roepen, herkomst onbekend.")
    }

    $r = @()
    $r += "Configuratie: commit $commit op branch $branch, " + $(if ($tag) { "getagd als $tag." } else { "niet getagd." })
    $r += "  Gelezen uit werkkopie $Pad."
    if ($vuil.Count -gt 0) {
        # Een commithash beschrijft de gebruikte configuratie alleen volledig als er niets openstond.
        $r += $(if ($vuil.Count -eq 1) { "  Let op: in die werkkopie stond een wijziging open, dus de commit hierboven" }
                else { "  Let op: in die werkkopie stonden $($vuil.Count) wijzigingen open, dus de commit hierboven" })
        $r += "  beschrijft niet alles wat er is doorgerekend:"
        foreach ($v in ($vuil | Select-Object -First 10)) { $r += "    $v" }
        if ($vuil.Count -gt 10) { $r += "    en nog $($vuil.Count - 10) andere" }
    }
    return $r
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

# Wat er in de LEESMIJ komt te staan, komt uit de doelmap zelf en niet uit de variantentabel bovenin.
# Een levering wordt in stappen gevuld, dus wat deze run heeft gekopieerd is niet hetzelfde als wat de
# ontvanger straks ziet. Basisjaar is geen variant en staat apart in de indeling.
$geleverd = [ordered]@{}
Get-ChildItem $Doel -Directory | Where-Object { $_.Name -ne 'Basisjaar' } | Sort-Object Name | ForEach-Object {
    $geleverd[$_.Name] = @(Get-ChildItem $_.FullName -Recurse -File).Count
}
$ontbreekt = @($Verwacht | Where-Object { $geleverd.Keys -notcontains $_ })
$onbekend  = @($geleverd.Keys | Where-Object { $Verwacht -notcontains $_ })

$regels = @()
$regels += "Oplevering RuimteScanner NL2120, issue #$Issue"
$regels += "Samengesteld op $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
$regels += ""
if ($geleverd.Count -eq 0) {
    $regels += "Zichtjaar $Zichtjaar. LET OP: deze map bevat op dit moment geen enkele variant."
} else {
    $lijst = Opsomming @($geleverd.Keys | ForEach-Object { "$_ ($($geleverd[$_]) bestanden)" })
    $regels += "Zichtjaar $Zichtjaar. Deze map bevat $lijst."
}
if ($ontbreekt.Count -gt 0) {
    $regels += "LET OP: deze levering is niet compleet. Verwacht en nog niet aanwezig: $(Opsomming $ontbreekt)."
}
$regels += ""
$regels += $(if ($Herkomst) { $Herkomst } else { Get-Herkomst $Werkkopie })
if ($Notitie) {
    $regels += ""
    $regels += "BIJ DEZE LEVERING"
    foreach ($r in $Notitie) { $regels += "  $r" }
}
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
$regels += ""
$regels += "  Vanaf 2060 staat de TIGRIS-claim voor wonen en werken stil; latere zichtjaren"
$regels += "  bouwen alleen nog terug wat de exogene opleggingen slopen."
$regels += ""
# Deze twee notities gelden voor elke oplevering en horen daarom hier en niet in de doelmap: de
# LEESMIJ daar wordt bij elke run overschreven, dus met de hand toegevoegde tekst verdwijnt.
$regels += "  CO2Flow_TovBasisjaar is het verschil tussen twee voorraden die ongeveer tweehonderd keer"
$regels += "  zo groot zijn als het verschil zelf. Een wijziging van een tiende procent in de"
$regels += "  zichtjaarvoorraad verandert deze indicator met ruim twintig procent. Lees hem daarom niet"
$regels += "  als een maat voor de omvang van een effect, en zet er bij een vergelijking tussen runs"
$regels += "  altijd CO2Stock_Zichtjaar naast, zodat de schaal zichtbaar blijft."
$regels += ""
$regels += "  De piekbuiberging en de sector Waterberging zijn twee verschillende grootheden. De kolommen"
$regels += "  Piekbuiberging_* gaan over de opgave bij een hevige bui in bestaand bebouwd gebied; de"
$regels += "  kolommen WaterbergingVeen en Sloop_WaterbergingVeen_* gaan over gealloceerde bergings-"
$regels += "  gebieden in het landelijk gebied, seizoensberging voor het veen. Ze hebben niets met elkaar"
$regels += "  te maken en horen niet bij elkaar opgeteld te worden. Tot #720 heetten ze allebei"
$regels += "  waterberging; in oudere leveringen staan de eerste dus als Waterberging_Vraag,"
$regels += "  Waterberging_RestvraagPositief en Waterberging_Afname."
$regels += ""
$regels += "  Lees Piekbuiberging_Dekkingsgraad nooit los van Piekbuiberging_Dekkingsgraad_Ongeklemd."
$regels += "  Opgave en aanbod worden per blok van 500 meter tegen elkaar weggestreept, en aanbod boven de"
$regels += "  opgave in datzelfde blok vervalt: op 2120 is dat in de NbS-variant bijna de helft van het"
$regels += "  aanbod, zichtbaar in Piekbuiberging_AanbodZonderOpgave_m3. De twee dekkingsgraden zijn de"
$regels += "  onder- en bovengrens van dezelfde uitkomst. De blokmaat zelf is een keuze zonder"
$regels += "  onderbouwing: op 100 meter komt de dekkingsgraad lager uit. Zie #720."
$regels | Set-Content (Join-Path $Doel 'LEESMIJ.txt') -Encoding UTF8

$totaal = Get-ChildItem $Doel -Recurse -File | Measure-Object Length -Sum
Write-Host ("klaar: {0} bestanden, {1} GB in {2}" -f $totaal.Count, [math]::Round($totaal.Sum/1GB,2), $Doel)
# Het scherm is de enige plek waar dit nog op te merken valt voordat de map wordt doorgestuurd.
if ($ontbreekt.Count -gt 0) {
    Write-Host ("LET OP: onvolledige levering, nog niet aanwezig: {0}" -f ($ontbreekt -join ', ')) -ForegroundColor Yellow
}
if ($onbekend.Count -gt 0) {
    Write-Host ("in de doelmap staan varianten die niet verwacht werden: {0}" -f ($onbekend -join ', ')) -ForegroundColor Yellow
}
