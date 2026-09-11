<#
================================================================================================
 RunIndicatoren.ps1: de indicatorenexport van RSopen NL2120, per variant en zichtjaar
================================================================================================

 WAT DIT SCRIPT DOET
   Leest de stand die de allocatie (Run2120.ps1) per zichtjaar heeft weggeschreven en rekent daar
   de indicatoren op uit: de kaarten, de tabellen en de gpkg's die de levering vormen. Het rekent
   dus niet opnieuw wat de allocatie deed. Per zichtjaar een aanroep van GeoDmsRun, gestuurd door
   de omgevingsvariabele ExportZichtjaar; per zichtjaar een log en een regel in status.tsv.
   Voordat er iets gerekend wordt toetst het script of alle invoer er staat (stand van elk
   zichtjaar, basisdata, variantdata) en zegt het welke stap ontbrekende invoer maakt.

 HOE START JE HET (vanuit een PowerShell-venster in de map batch)
   De levering: alle varianten, zichtjaar 2120, tabellen per landschap en landsdekkend:
       .\RunIndicatoren.ps1 -Varianten BAU,BAU2,NbSGenuanceerd -IndicatorRegio Landschap
   Een variant op de landelijke indeling:
       .\RunIndicatoren.ps1 -Varianten BAU
   Meerdere zichtjaren:
       .\RunIndicatoren.ps1 -Varianten BAU -Zichtjaren Y2040,Y2120
   Daarna de oplevering samenstellen met batch\MaakOplevering.ps1.

 INSTELLINGEN

   A. Parameters van dit script (commandoregel; standaardwaarden in het blok param() hieronder).
      -Exe, -Cfg, -LogDir   Zoals bij Run2120.ps1: de geinstalleerde GeoDMS, cfg\main.dms van de
                            werkkopie, en de logmap.
      -Scenario             Standaard WLO_hoog; casusnamen zijn <scenario>_<variant>.
      -Varianten            Lijst, bijvoorbeeld BAU,BAU2,NbSGenuanceerd. De namen staan in
                            cfg\main\VariantParameters\VariantK.dms, kolom name.
      -Zichtjaren           Standaard Y2120. Meerdere kan: Y2040,Y2120. Het basisjaar kan niet
                            (ExportZichtjaar=Basisjaar valt om; de basisjaarkaarten komen vanzelf mee).
      -IndicatorRegio       Op welke indeling de tabel Indicatoren_<regio>.csv aggregeert: NL,
                            Provincie, COROP, Gemeente, NVM, Landschap of een van de vier
                            Landschap_<naam>. De landsdekkende tabel NationaleIndicatoren komt hoe dan
                            ook mee, dus Landschap levert beide en hoeft niet ook op NL.
      -Gebundeld            Alle varianten van een zichtjaar in een GeoDmsRun-proces, na elkaar; scheelt
                            het inlezen van wat de casussen delen. Gebruik dit, en draai NOOIT meerdere
                            processen naast elkaar op dezelfde LocalData: ze botsen op bestanden die
                            ze allebei openen.
      -GeenToets            Slaat de toets op de invoer over. Alleen voor wie precies weet wat er staat.

   B. Omgevingsvariabelen die dit script zelf zet: StandAllocatieOntkoppeld=TRUE (stand uit de tifs),
      VariantDataOntkoppeld=TRUE, IndicatorRegio en ExportZichtjaar. LocalDataProjDir wordt gewist,
      GeoDMS leidt het pad af uit LocalDataDir plus de mapnaam boven cfg.

   C. Wat dit script NIET regelt en je vooraf moet nalopen:
      - De stand moet er staan voor ELK zichtjaar tot en met het exportzichtjaar, want cumulatieve
        indicatoren (contante waarden, koolstof, sterfte) rekenen alle voorgaande zichtjaren mee.
      - De basisdata van WriteBasedata/Generate_Run3 en Generate_Run4_IndicatorenData en de
        variantdata van WriteVariantData. Run2120.ps1 maakt ze allemaal; de toets hieronder meldt
        wat ontbreekt en welk item het maakt.
      - De legenda's (Export/Legendas/Schrijf) schrijft dit script zelf, ze zijn casusonafhankelijk.
      - De schakelaars in cfg\main\ModelParameters.dms, zie blok B van Run2120.ps1.

 BEKEND PROBLEEM
   Een run op de landschapsindeling rekent na het schrijven van de landschapstabel de WP5-
   pandtypering opnieuw uit (SourceData/Vastgoed/BAG/.../AfleidingPandType/Write_WP5) en wacht dan
   een half uur op een schrijfhandle die het proces zelf al open heeft, of blijft daarin hangen met
   0 CPU en een log dat midden in een regel stopt. De uitvoer tot dat moment staat gewoon op schijf.
   Blijft het proces hangen, stop het dan en draai de rest (generates/Indicatoren_PerNederland,
   generates/ClaimRealisatie*) op -IndicatorRegio NL na; die items zijn onafhankelijk van de
   indeling. Op NL treedt het niet op. Zie het issue over de WP5-herberekening.

 ALS HET MISGAAT
   status.tsv (kolom exit) en het log van de stap; regels met [E] zijn de fouten. Exit 2 is een
   configuratiefout, exit 1 een rekenfout of ontbrekend bestand; exit 0 met [E]-regels telt ook als
   mislukt. Een tabel (csv) wordt kolom voor kolom geschreven, dus een csv kan na een fout minder
   kolommen hebben dan de configuratie; vergelijk de kopregel met die van een gave tabel.
================================================================================================
#>
[CmdletBinding()]
param(
    [string]   $Exe        = 'C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe',
    [string]   $Cfg        = 'C:\ProjDir\RSopen_NL2120_productie\cfg\main.dms',
    [string]   $LocalData  = 'C:\LocalData\RSopen_NL2120_productie',
    [string]   $LogDir     = 'C:\ProjDir\RSopen_NL2120_productie\batch\log\indicatoren',
    [string]   $Scenario   = 'WLO_hoog',
    [string[]] $Varianten  = @('BAU','BAU2'),
    [string[]] $Zichtjaren = @('Y2120'),
    [ValidateSet('NL','Provincie','COROP','Gemeente','NVM','Landschap',
                 'Landschap_Kust','Landschap_Rivieren','Landschap_Veen','Landschap_Zand')]
    [string]   $IndicatorRegio = 'NL',
    [switch]   $Gebundeld,
    [switch]   $GeenToets
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Exe)) { throw "GeoDmsRun niet gevonden: $Exe" }
if (-not (Test-Path $Cfg)) { throw "Configuratie niet gevonden: $Cfg" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

$env:StandAllocatieOntkoppeld = 'TRUE'
$env:VariantDataOntkoppeld    = 'TRUE'
$env:IndicatorRegio           = $IndicatorRegio
Remove-Item Env:\LocalDataProjDir -ErrorAction SilentlyContinue

$status = Join-Path $LogDir 'status.tsv'
if (-not (Test-Path $status)) { "tijd`tstap`texit`tseconden" | Set-Content $status -Encoding UTF8 }

function Write-Regel([string]$T) { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $T" }

function Get-VariantKolom([string]$CfgPad, [string]$Kolom) {
    # Een kolom uit VariantK.dms als tabel variant -> waarde, geparsed uit de tekst omdat dat
    # milliseconden kost en een GeoDmsRun een minuut.
    $vk = Join-Path (Split-Path $CfgPad -Parent) 'main\VariantParameters\VariantK.dms'
    if (-not (Test-Path $vk)) { throw "VariantK.dms niet gevonden naast $CfgPad" }
    $tekst = Get-Content $vk -Raw
    $kolommen = @{}
    foreach ($naam in @('name', $Kolom)) {
        $m = [regex]::Match($tekst, "attribute<[^>]+>\s+$naam\s*:\s*\[(.*?)\]", 'Singleline')
        if (-not $m.Success) { throw "kolom $naam niet gevonden in VariantK.dms" }
        $kolommen[$naam] = @([regex]::Matches($m.Groups[1].Value, "'([^']*)'") | ForEach-Object { $_.Groups[1].Value })
    }
    $t = @{}
    for ($i = 0; $i -lt $kolommen['name'].Count; $i++) { $t[$kolommen['name'][$i]] = $kolommen[$Kolom][$i] }
    return $t
}

function Get-Zichtjaren {
    # Alle zichtjaren uit de configuratie, nodig om te toetsen of elke stand tot aan het
    # exportzichtjaar er staat. Zelfde aanroep als in Run2120.ps1.
    $log = Join-Path $LogDir 'zichtjaren.log'
    $uit = & $Exe "/L$log" $Cfg '@statistics' '/Classifications/Time/Zichtjaar/YearRange_rel' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Kon de zichtjaren niet uit de configuratie lezen, zie $log" }
    $blok  = (($uit -join "`n") -split 'clipboard:')[-1]
    $jaren = @()
    foreach ($regel in ($blok -split "`n")) {
        if ($regel -match '^\s*([\d.,]+)\s') { $j = $matches[1] -replace '[^\d]', ''; if ($j.Length -eq 4) { $jaren += "Y$j" } }
    }
    $jaren = $jaren | Select-Object -Unique
    if ($jaren.Count -eq 0) { throw "Geen zichtjaren gevonden in de configuratie" }
    return $jaren
}

function Test-Invoer {
    # De toets uit ObjectVision/RSopen#816: zeg vooraf wat er ontbreekt en welk item het maakt, in
    # plaats van na drie kwartier rekenen om te vallen. Een representatief bestand per stap, geen
    # volledige inventaris; wat de configuratie zelf met een fingerprint bewaakt (verwervings- en
    # sloopkosten, BRP, NBP, MNP) maakt zij bij een verouderd bestand zelf opnieuw.
    $alleJaren = Get-Zichtjaren
    $leen  = Get-VariantKolom $Cfg 'StandVanVariant'
    $hydro = Get-VariantKolom $Cfg 'Hydrologie_Levering'
    $opbr  = Get-VariantKolom $Cfg 'OpbrengstenVariant_Wonen'

    $eisen = @()
    $eisen += ,@('BaseData\Vastgoed\VolledigeTabel_*\WP5\*.mmd',           'WP5-pandtypering',           '/WriteBasedata/Generate_Run1')
    $eisen += ,@('BaseData\Grondgebruik\BBG\BBG*_25m_Modus_*.tif',         'BBG-vergridding',            '/WriteBasedata/Generate_Run2')
    $eisen += ,@('BaseData\Grondgebruik\LGN\*.tif',                        'LGN-groenfracties',          '/WriteBasedata/Generate_Run2')
    $eisen += ,@('BaseData\StandBasisjaar\Wonen\*.tif',                    'stand basisjaar',            '/WriteBasedata/Generate_Run3')
    $eisen += ,@('BaseData\Vastgoed\WP2xVSSH_Proxy\*',                     'woningsubsector-proxies',    '/WriteBasedata/Generate_Run3')
    $eisen += ,@('BaseData\Vastgoed\Sloopkosten_Woningen_*.tif',           'sloopkosten',                '/WriteBasedata/Generate_Run3')
    $eisen += ,@('BaseData\Grondgebruik\BGT\GroenOpp_*.tif',               'BGT groen, bruin, verhard',  '/WriteBasedata/Generate_Run4_IndicatorenData')
    $eisen += ,@('BaseData\Grondgebruik\BGT\*Capaciteit_*.tif',            'BGT bergingscapaciteiten',   '/WriteBasedata/Generate_Run4_IndicatorenData')
    foreach ($v in $Varianten) {
        if (-not $opbr.ContainsKey($v)) { throw "Variant $v staat niet in VariantK.dms (kolom name); bekende varianten: $($opbr.Keys -join ', ')" }
        $standVan = if ($leen[$v]) { $leen[$v] } else { $v }
        foreach ($y in $Zichtjaren) {
            $tot = $alleJaren.IndexOf($y)
            if ($tot -lt 0) { throw "Zichtjaar $y staat niet in de configuratie ($($alleJaren -join ', '))" }
            foreach ($j in $alleJaren[0..$tot]) {
                $eisen += ,@("Allocatie\${Scenario}_$standVan\Stand$j\OP_rel_*.tif", "stand $j van ${Scenario}_$standVan (variant $v)", "batch\Run2120.ps1, stap allocatie-$standVan-$j")
            }
        }
        $eisen += ,@("BaseData\Landbouw\WWL_Opbrengstderving\$($hydro[$v])_*.tif", "opbrengstderving van levering $($hydro[$v]) (variant $v)", "/WriteVariantData/per_Variant/$v/Generate_Run2")
        $eisen += ,@("VariantData\Vastgoed\Opbrengsten_perOP\$($opbr[$v])\*.tif", "opbrengsten per pakket, set $($opbr[$v]) (variant $v)", "/WriteVariantData/per_Variant/$v/Generate_Run1")
        $eisen += ,@("VariantData\Grondgebruik\BGT\EvidentBenut_*_$v.tif",         "evident benut (variant $v)",                     "/WriteVariantData/per_Variant/$v/Generate_Run1")
    }

    $mis = @()
    foreach ($e in $eisen) {
        $pad = Join-Path $LocalData $e[0]
        if (-not (Get-ChildItem $pad -ErrorAction SilentlyContinue | Select-Object -First 1)) { $mis += ,$e }
    }
    if ($mis.Count -gt 0) {
        Write-Regel "GESTOPT: invoer ontbreekt in $LocalData. Maak hem eerst met het genoemde item of script:"
        foreach ($m in $mis) { Write-Host ("   {0,-60} {1,-50} {2}" -f $m[0], $m[1], $m[2]) }
        throw "Invoer voor de indicatoren ontbreekt ($($mis.Count) van $($eisen.Count) toetsen)"
    }
    Write-Regel "controle  : invoer aanwezig ($($eisen.Count) toetsen)"
}

$totaal = [Diagnostics.Stopwatch]::StartNew()
Write-Regel "config    : $Cfg"
Write-Regel "localdata : $LocalData"
Write-Regel "varianten : $($Varianten -join ', ')"
Write-Regel "zichtjaren: $($Zichtjaren -join ', ')"
Write-Regel "regio     : $IndicatorRegio (de landelijke tabel komt hoe dan ook mee, #705)"

if (-not $GeenToets) { Test-Invoer }

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
        Write-Regel "log       : $log"
        $fouten | Select-Object -First 15 | ForEach-Object { Write-Host "   $($_.Line)" }
        throw "Stap '$stap' mislukt: $reden"
    }
    Write-Regel "klaar     : $stap ($([math]::Round($sec/60,1)) min)"
}

# De legenda's zijn casusonafhankelijk en kosten een seconde; zonder deze bestanden mist de
# oplevering de klassenamen bij elke klassekaart (MaakOplevering.ps1 meldt dat als waarschuwing).
$eerste = "/Indicatoren/${Scenario}_$($Varianten[0])/Zichtjaren/Export/Legendas/Schrijf"
Invoke-Export "legendas" @($eerste)

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
Write-Regel "volgende  : batch\MaakOplevering.ps1 -Doel <opleveringsmap> -Issue <nummer>"
