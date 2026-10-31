<#
.SYNOPSIS
    Toetst of een reeks items in een configuratie oplost (alle namen gevonden, alle domeinen en
    eenheden passend), zonder ze uit te rekenen, en noemt de bestanden die ze lezen en schrijven.

.DESCRIPTION
    GeoDMS lost voor een opgevraagd item eerst alle namen in zijn keten op en begint daarna te
    rekenen. Dit script vraagt de items niet op maar laat GeoDmsRun ze beschrijven met
    @sourcedescr: dan wordt de keten wel opgelost, met een [E]-regel in het log voor elke naam die
    niet bestaat, maar er wordt niets uitgerekend en niets geschreven. Per item geeft
    @sourcedescr bovendien de opslag die de keten direct noemt: wat ze leest en wat ze schrijft.
    Achter een bestand dat de keten zelf schrijft kijkt @sourcedescr niet verder, dus wat zo'n
    bestand op zijn beurt leest staat er niet bij; de lijst is geen volledige bronnenlijst.

    Waarom niet gewoon opvragen: GeoDmsRun rekent een opgevraagd item echt uit, ook als het zelf
    geen storage heeft, en schrijft onderweg elke leverancier met een StorageName. Een parameter of
    een Per_Regio is daardoor geen goedkope toets als de keten zwaar is. Zie de skill rs-draaien,
    trap 1. Het opvragen stoppen zodra de regel "{ Updating::" in het /L-log verschijnt werkt ook
    niet: GeoDmsRun schrijft dat log gebufferd, dus de regel staat er pas als er genoeg nieuwe
    regels bij zijn gekomen. Op 2026-10-28 stond hij er pas na anderhalve minuut, en had het proces
    intussen 90 GB vastgelegd.

    GeoDmsRun geeft na @sourcedescr ook exit 0 als een naam niet bestaat; de uitslag komt daarom uit
    de [E]-regels in het log. Het script stopt het proces als het meer dan MaxGB geheugen vastlegt
    of langer dan MaxSeconden duurt; dat hoort bij een beschrijving niet te gebeuren.

    Wat dit niet toetst: data. Een ontbrekend bestand of een lege kaart komt er niet in boven,
    behalve waar de configuratie het bestand al bij het oplossen opent (een mmd-woordenboek, de
    kop van een tif). Op een lege LocalData geeft dat altijd foutregels over ontbrekende
    ontkoppelde bestanden; leg die naast dezelfde toets op een stand waarvan je weet dat hij werkt.
    En een meta-expressie lost alleen de tak op die bij de huidige schakelaars hoort.

    Het script neemt de omgevingsvariabelen van de aanroeper over. Zet ze zelf, want een
    meta-expressie kiest zijn tak daarop: StandAllocatieOntkoppeld, VariantDataOntkoppeld,
    IndicatorenOntkoppeld, TabellenUitExport, ExportZichtjaar, IndicatorRegio, NatuurOpleggen.
    Zonder LocalDataProjDir leidt GeoDMS de LocalData af uit de mapnaam boven cfg.

.EXAMPLE
    $env:StandAllocatieOntkoppeld = 'TRUE'; $env:VariantDataOntkoppeld = 'TRUE'
    .\naamcontrole.ps1 -Config 'C:\pad\naar\Toets\cfg\main.dms' -Items '/WriteVariantData/per_Variant/BAU/Generate_Run2', '/Indicatoren/WLO_hoog_BAU/Zichtjaren/Export/generates/Generate_Alles' -Bestanden
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$Items,

    [Parameter(Mandatory = $true)]
    [string]$Config,

    # Niet meer nodig: @sourcedescr schrijft niets. Blijft bestaan zodat oudere aanroepen werken.
    [switch]$EigenLocalData,

    # De vaste versie voor dit project, zoals in run-item.ps1; @sourcedescr bestaat sinds 20.17.0.
    [string]$Version = "20.23.1.m",

    [string]$LogDir = "$env:TEMP\rsopen-check",

    # Noodremmen. Een beschrijving rekent niets, dus elk van beide wijst op iets onverwachts.
    [int]$MaxSeconden = 600,
    [int]$MaxGB = 16,

    # Schrijf de volledige lijst gelezen en geschreven bestanden naar een tekstbestand naast het log.
    [switch]$Bestanden,

    [int]$PollMs = 500
)

$ErrorActionPreference = "Stop"

$exe = Join-Path "C:\Program Files\ObjectVision" "GeoDms$Version\GeoDmsRun.exe"
if (-not (Test-Path $exe)) { throw "GeoDmsRun niet gevonden: $exe" }
$Config = [System.IO.Path]::GetFullPath($Config)
if (-not (Test-Path $Config)) { throw "Config niet gevonden: $Config" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

$stam = Join-Path $LogDir ("{0}_naamcontrole" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$log  = "$stam.log"
$uit  = "$stam.uitvoer.txt"
$err  = "$stam.stderr.txt"

Write-Host "build : GeoDms$Version"
Write-Host "config: $Config"
Write-Host "items : $($Items.Count)"
Write-Host "log   : $log"

# Start-Process plakt de argumenten met spaties aan elkaar, dus elk argument krijgt zelf aanhalingstekens.
$argumenten = @("`"/L$log`"", "`"$Config`"")
foreach ($i in $Items) { $argumenten += '@sourcedescr'; $argumenten += "`"$i`"" }
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$proc = Start-Process -FilePath $exe -ArgumentList $argumenten -PassThru -NoNewWindow -RedirectStandardOutput $uit -RedirectStandardError $err
$null = $proc.Handle   # zonder deze regel is ExitCode na afloop leeg

$gestopt = $null; $piekGB = 0
while (-not $proc.HasExited) {
    $proc.Refresh()
    $gb = [math]::Round($proc.PrivateMemorySize64 / 1GB, 1)
    if ($gb -gt $piekGB) { $piekGB = $gb }
    if ($gb -gt $MaxGB) { $gestopt = "meer dan $MaxGB GB vastgelegd"; Stop-Process -Id $proc.Id -Force; break }
    if ($sw.Elapsed.TotalSeconds -gt $MaxSeconden) { $gestopt = "langer dan $MaxSeconden s"; Stop-Process -Id $proc.Id -Force; break }
    Start-Sleep -Milliseconds $PollMs
}
$proc.WaitForExit(10000) | Out-Null
$sw.Stop()

$regels = if (Test-Path $log) { @(Get-Content -LiteralPath $log) } else { @() }
$fouten = @($regels | Where-Object { $_ -match '\[E\]' })
$schrijf = @($regels | Where-Object { $_ -match '\[storage write\]' })
$tekst  = if (Test-Path $uit) { Get-Content -LiteralPath $uit -Raw } else { '' }

# Per item een blok "@sourcedescr <pad>", met daaronder de vier lijsten van de detailpagina.
$beschreven = 0; $gelezen = @{}; $geschreven = @{}; $lijst = $null
foreach ($r in ($tekst -split "`r?`n")) {
    if ($r -match '^@sourcedescr ') { $beschreven++; $lijst = $null; continue }
    if ($r -match '^Read Only Storage Managers:') { $lijst = 'lees'; continue }
    if ($r -match '^Non-Read Only Storage Managers:') { $lijst = 'schrijf'; continue }
    if ($r -match '^\S.*:\s*$') { $lijst = $null; continue }
    $m = [regex]::Match($r, '^- name="([^"]+)"')
    if ($m.Success -and $lijst -eq 'lees') { $gelezen[$m.Groups[1].Value] = 1 }
    if ($m.Success -and $lijst -eq 'schrijf') { $geschreven[$m.Groups[1].Value] = 1 }
}

$secs = [math]::Round($sw.Elapsed.TotalSeconds, 1)
Write-Host ""
Write-Host "beschreven $beschreven van $($Items.Count) items in $secs s, piek $piekGB GB, $(if ($gestopt) { "GESTOPT: $gestopt" } else { "exit $($proc.ExitCode)" })"
Write-Host "opslag   : $($gelezen.Count) alleen-lezen, $($geschreven.Count) schrijvend, zoals de keten ze direct noemt (er is niets aangeraakt)"

if ($Bestanden) {
    $lijstPad = "$stam.bestanden.txt"
    @('# gelezen') + @($gelezen.Keys | Sort-Object) + @('', '# geschreven') + @($geschreven.Keys | Sort-Object) | Set-Content -LiteralPath $lijstPad -Encoding UTF8
    Write-Host "lijst    : $lijstPad"
}

if ($fouten.Count -gt 0) {
    Write-Host ""
    Write-Host "foutregels uit het log ($($fouten.Count)):"
    $fouten | Select-Object -First 40 | ForEach-Object { Write-Host "  $($_.Substring(0, [Math]::Min(300, $_.Length)))" }
    if ($fouten.Count -gt 40) { Write-Host "  ... en nog $($fouten.Count - 40) regels" }
}
if ($schrijf.Count -gt 0) {
    Write-Host ""
    Write-Host "LET OP: het log meldt $($schrijf.Count) keer storage write; een beschrijving hoort niets te schrijven:" -ForegroundColor Yellow
    $schrijf | Select-Object -First 10 | ForEach-Object { Write-Host "  $($_.Substring(0, [Math]::Min(300, $_.Length)))" -ForegroundColor Yellow }
}

$ok = (-not $gestopt) -and ($fouten.Count -eq 0) -and ($beschreven -eq $Items.Count) -and ($schrijf.Count -eq 0)
exit $(if ($ok) { 0 } else { 1 })
