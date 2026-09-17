<#
.SYNOPSIS
    Toetst in een kopie van cfg met een eigen LocalData of een reeks items oplost, zonder ze uit
    te rekenen.

.DESCRIPTION
    GeoDmsRun lost eerst voor alle opgevraagde items de namen op, met in het log een regel
    "[progress]Item <pad>" per item en eventuele [E]-regels, en begint daarna te rekenen met
    een regel "{ Updating::[[<pad>]]". Dit script start GeoDmsRun, leest het log met gedeelde
    toegang (GeoDmsRun houdt het tijdens de run open voor schrijven) en stopt het proces op
    zijn PID zodra de eerste Updating-regel verschijnt.

    Waarom: GeoDmsRun rekent een opgevraagd item echt uit, ook als het zelf geen storage heeft,
    en schrijft onderweg elke leverancier met een StorageName. Een parameter of een Per_Regio
    is daardoor geen goedkope toets als de keten zwaar is. Zie de skill rs-draaien, trap 1.

    ALLEEN OP EEN EIGEN LOCALDATA. De rekenronde begint in dezelfde seconde als de laatste
    resolutieregel, en GeoDMS verwijdert het bestand van een schrijvend item aan het begin van
    dat item, niet pas als de data klaar is. Gemeten op 2026-09-17: het script stopte binnen
    200 ms na de eerste Updating-regel, het log meldde geen storage write, en toch stond er van
    een tif van 6,4 MB nog 84 KB. Daarom weigert het script zonder -EigenLocalData, en meldt
    het na afloop aan welk item GeoDMS was begonnen. Vraag dat item daarna volledig op, of gooi
    de kopie weg.

    Verder toetst dit alleen namen en domeinen, geen data: een ontbrekend bestand of een lege
    kaart komt er niet in boven.

    Het script neemt de omgevingsvariabelen van de aanroeper over. Zet ze zelf, want een
    meta-expressie kiest zijn tak daarop: StandAllocatieOntkoppeld, VariantDataOntkoppeld,
    IndicatorenOntkoppeld, TabellenUitExport, ExportZichtjaar, IndicatorRegio. Zonder
    LocalDataProjDir leidt GeoDMS de LocalData af uit de mapnaam boven cfg.

.EXAMPLE
    $env:StandAllocatieOntkoppeld = 'TRUE'; $env:VariantDataOntkoppeld = 'TRUE'; $env:ExportZichtjaar = 'Y2120'
    .\resolutie.ps1 -EigenLocalData -Config 'C:\pad\naar\Toets\cfg\main.dms' -Items '/Indicatoren/WLO_hoog_BAU/Zichtjaren/Y2120/Dichtheid/Wonen/Per_NL', '/Indicatoren/WLO_hoog_BAU/Zichtjaren/Export/generates/Kaarten_lijst'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$Items,

    # Bewust zonder standaard: de configuratie van de werkkopie zelf schrijft in de gedeelde LocalData.
    [Parameter(Mandatory = $true)]
    [string]$Config,

    # Verklaart dat de LocalData van deze configuratie een wegwerpkopie is.
    [switch]$EigenLocalData,

    # De vaste versie voor dit project, zoals in run-item.ps1.
    [string]$Version = "20.17.0.m",

    [string]$LogDir = "$env:TEMP\rsopen-check",

    # Noodrem voor als er nooit een Updating-regel komt.
    [int]$MaxSeconden = 300,

    [int]$PollMs = 200
)

$ErrorActionPreference = "Stop"

if (-not $EigenLocalData) {
    throw "Geweigerd: het eerste item wordt al bijgewerkt voordat dit script kan stoppen, en een bestand van dat item kan daarna half geschreven zijn. Draai alleen op een kopie van cfg met een eigen LocalData en geef dan -EigenLocalData mee."
}

$exe = Join-Path "C:\Program Files\ObjectVision" "GeoDms$Version\GeoDmsRun.exe"
if (-not (Test-Path $exe)) { throw "GeoDmsRun niet gevonden: $exe" }
$Config = [System.IO.Path]::GetFullPath($Config)
if (-not (Test-Path $Config)) { throw "Config niet gevonden: $Config" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

$log = Join-Path $LogDir ("{0}_resolutie.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
if (Test-Path $log) { [System.IO.File]::Delete($log) }

function Read-Log {
    if (-not (Test-Path $log)) { return "" }
    try {
        $fs = [System.IO.File]::Open($log, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try { return (New-Object System.IO.StreamReader($fs)).ReadToEnd() } finally { $fs.Close() }
    } catch { return "" }
}

Write-Host "build : GeoDms$Version"
Write-Host "config: $Config"
Write-Host "items : $($Items.Count)"
Write-Host "log   : $log"

# Start-Process plakt de argumenten met spaties aan elkaar, dus elk argument krijgt zelf aanhalingstekens.
$argumenten = @("`"/L$log`"", "`"$Config`"") + @($Items | ForEach-Object { "`"$_`"" })
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$proc = Start-Process -FilePath $exe -ArgumentList $argumenten -PassThru -WindowStyle Hidden
$null = $proc.Handle   # zonder deze regel is ExitCode na afloop leeg

$gestopt = $false
while (-not $proc.HasExited) {
    if ((Read-Log) -match '\{ Updating::\[\[') {
        Stop-Process -Id $proc.Id -Force
        $gestopt = $true
        break
    }
    if ($sw.Elapsed.TotalSeconds -gt $MaxSeconden) {
        Stop-Process -Id $proc.Id -Force
        $gestopt = $true
        Write-Host "Na $MaxSeconden s nog geen rekenronde; proces gestopt." -ForegroundColor Yellow
        break
    }
    Start-Sleep -Milliseconds $PollMs
}
$proc.WaitForExit(10000) | Out-Null
$sw.Stop()

$tekst    = Read-Log
$regels   = $tekst -split "`r?`n"
$opgelost = @($regels | Where-Object { $_ -match '\[progress\]Item /' })
$fouten   = @($regels | Where-Object { $_ -match '\[E\]' })
$schrijf  = @($regels | Where-Object { $_ -match '\[storage write\]' })
$begonnen = [regex]::Match($tekst, '\{ Updating::\[\[([^\]]*)\]\]')
$secs     = [math]::Round($sw.Elapsed.TotalSeconds, 1)
$afloop   = if ($gestopt) { "gestopt op PID $($proc.Id)" } else { "zelf geeindigd met exit $($proc.ExitCode)" }

Write-Host ""
Write-Host "resolutieregels $($opgelost.Count) voor $($Items.Count) items in $secs s, proces $afloop"

if ($fouten.Count -gt 0) {
    Write-Host ""
    Write-Host "foutregels uit het log:"
    $fouten | Select-Object -First 40 | ForEach-Object { Write-Host "  $($_.Substring(0, [Math]::Min(300, $_.Length)))" }
    if ($fouten.Count -gt 40) { Write-Host "  ... en nog $($fouten.Count - 40) regels" }
}

if ($begonnen.Success -and $gestopt) {
    Write-Host ""
    Write-Host "GeoDMS was begonnen aan $($begonnen.Groups[1].Value)." -ForegroundColor Yellow
    Write-Host "Schrijft die keten een bestand, dan kan dat nu half geschreven zijn: vraag het item volledig op of gooi de kopie weg." -ForegroundColor Yellow
}
if ($schrijf.Count -gt 0) {
    Write-Host ""
    Write-Host "Het log meldt bovendien $($schrijf.Count) keer storage write:" -ForegroundColor Yellow
    $schrijf | Select-Object -First 10 | ForEach-Object { Write-Host "  $($_.Substring(0, [Math]::Min(300, $_.Length)))" -ForegroundColor Yellow }
}

$ok = $begonnen.Success -and ($fouten.Count -eq 0) -and ($opgelost.Count -ge $Items.Count)
if (-not $begonnen.Success) {
    Write-Host ""
    Write-Host "Geen rekenronde bereikt: de resolutie is niet afgerond. Lees het log." -ForegroundColor Yellow
}
exit $(if ($ok) { 0 } else { 1 })
