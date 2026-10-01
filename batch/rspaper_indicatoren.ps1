# Indicatoren voor het paper (RS_paper, Noord-Holland): de kaarten en tabellen van grondgebruik, wonen en werken
# en de claimrealisatie, per variant voor zichtjaar 2050. Niet de volledige export van RunIndicatoren.ps1: die
# vraagt de landgebruikskaart en de domeinen water, natuur, landbouw en koolstof, en daarvoor maakt deze projectlijn
# de basisdata niet (ModelParameters/Indicatoren/Domein, kolom RSpaper).
param(
    [string[]] $Varianten = @('BAU','HA1','HA2','HA3','HA4'),
    [string]   $Zichtjaar = 'Y2050',
    [string]   $Regio     = 'COROP',
    [string[]] $Items     = @(
        'Verstedelijking','VerstedelijkingInABCD','Verstedelijking_Zichtjaar',
        'Dichtheid_Wonen','Dichtheid_Wonen_Zichtjaar','PandFootprint_Wonen','Bouwwijze_Areaal',
        'Grondexploitatie_Saldo','Grondexploitatie_Nieuwbouw_Ha','Grondexploitatie_Post_Opbrengsten','Grondexploitatie_Post_Verwerving','Grondexploitatie_Post_Sloop',
        'Inbreiding_WoningenErbij','Inbreiding_BestaandBebouwdGebied',
        'Dichtheid_Werken_Pandfootprint_ha','Dichtheid_Werken_Banen_m2','PandFootprint_Werken','Dichtheid_Werken_Banen_ha_Zichtjaar',
        'ClaimRealisatie','Claims_Reeks'),
    [string]   $Tag       = 'kaarten',
    [string]   $Cfg       = 'C:\ProjDir\RSopen_RSpaper\cfg\main.dms',
    [string]   $LogDir    = 'C:\ProjDir\RSopen_RSpaper\batch\log\indicatoren'
)
$exe    = 'C:\Program Files\ObjectVision\GeoDms20.20.0.m\GeoDmsRun.exe'
$cfg    = $Cfg
$logdir = $LogDir
New-Item -ItemType Directory -Force -Path $logdir | Out-Null
$status = Join-Path $logdir 'status.tsv'
if (-not (Test-Path $status)) { "tijd`tstap`texit`tseconden`tfoutregels" | Set-Content $status -Encoding UTF8 }

$env:LocalDataProjDir         = $null
$env:StandAllocatieOntkoppeld = 'TRUE'
$env:VariantDataOntkoppeld    = 'TRUE'
$env:IndicatorenOntkoppeld    = 'TRUE'
$env:TabellenUitExport        = 'FALSE'
$env:IndicatorRegio           = $Regio
$env:ExportZichtjaar          = $Zichtjaar

foreach ($v in $Varianten) {
    $stap = "$Tag-$v-$Zichtjaar"
    $log  = Join-Path $logdir ("{0}_{1}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'), $stap)
    $paden = @($Items | ForEach-Object { "/Indicatoren/WLO_hoog_$v/Zichtjaren/Export/generates/$_" })
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $exe "/L$log" '/S1' '/S2' '/S3' $cfg @paden 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $sec  = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    $fout = @(Select-String -Path $log -Pattern '\[E\]' -ErrorAction SilentlyContinue)
    "{0}`t{1}`t{2}`t{3}`t{4}" -f (Get-Date -Format 's'), $stap, $code, $sec, $fout.Count | Add-Content $status -Encoding UTF8
    "[{0}] {1}: exit {2}, {3} s, {4} foutregels, log {5}" -f (Get-Date -Format 'HH:mm:ss'), $stap, $code, $sec, $fout.Count, $log
    $fout | Select-Object -First 8 | ForEach-Object { '   ' + $_.Line.Substring(0, [Math]::Min(260, $_.Line.Length)) }
}
