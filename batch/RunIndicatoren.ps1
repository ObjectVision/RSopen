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
   De levering: alle varianten, zichtjaar 2120, de vier landschapstabellen en landsdekkend:
       .\RunIndicatoren.ps1 -Varianten BAU,BAU2,NbSGenuanceerder -IndicatorRegio Landschappen
   Alleen de vier landschapstabellen, bij een levering die de rest al heeft:
       .\RunIndicatoren.ps1 -Varianten BAU,BAU2,NbSGenuanceerder -IndicatorRegio Landschappen -AlleenLandschapstabellen
   Een variant op de landelijke indeling:
       .\RunIndicatoren.ps1 -Varianten BAU
   Meerdere zichtjaren:
       .\RunIndicatoren.ps1 -Varianten BAU -Zichtjaren Y2040,Y2120
   Ontkoppeld (#824): de zichtjaren voor het exportzichtjaar elk in een eigen proces, daarna de
   export van het exportzichtjaar, die dan alleen dat jaar rekent:
       .\RunIndicatoren.ps1 -Varianten BAU,BAU2,NbSGenuanceerder -IndicatorRegio Landschappen -Ontkoppeld
   Alleen het exportzichtjaar opnieuw (bijvoorbeeld een tabel na een reparatie), met de ketens van
   een eerdere ontkoppelde run:
       .\RunIndicatoren.ps1 -Varianten BAU -IndicatorRegio Landschappen -Ontkoppeld -AlleenExportZichtjaar
   De tabellen uit de geschreven export (#824): eerst alle kaarten, dan in een eigen proces de tabellen,
   die die kaarten teruglezen in plaats van de indicatoren opnieuw te rekenen:
       .\RunIndicatoren.ps1 -Varianten BAU,BAU2,NbSGenuanceerder -IndicatorRegio Landschappen -Ontkoppeld -TabellenUitExport
   Alleen de landschapstabellen opnieuw, op de kaarten van een eerdere export van hetzelfde zichtjaar:
       .\RunIndicatoren.ps1 -Varianten BAU -IndicatorRegio Landschappen -AlleenLandschapstabellen -TabellenUitExport
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
                            Provincie, COROP, Gemeente, NVM, een van de vier Landschap_<naam>, of
                            Landschappen: de vier aangeleverde, overlappende landschapsgebieden van
                            #760 na elkaar, een run per gebied, elk Indicatoren_Landschap_<naam>.csv.
                            De landsdekkende tabel NationaleIndicatoren komt met de eerste run mee.
                            De partitie van #705 (Landschap) is sinds 13 september 2026 geen optie meer.
      -AlleenLandschapstabellen  Alleen de regionale tabel per run, zonder grids, landelijke tabel en
                            claimrealisatie; voor een levering die die al heeft. Bij Landschappen
                            draagt anders de eerste run de volledige export en de drie volgende alleen
                            hun tabel, want al het andere hangt niet van de indeling af.
      -Gebundeld            Alle varianten van een zichtjaar in een GeoDmsRun-proces, na elkaar; scheelt
                            het inlezen van wat de casussen delen. Gebruik dit, en draai NOOIT meerdere
                            processen naast elkaar op dezelfde LocalData: ze botsen op bestanden die
                            ze allebei openen.
      -Ontkoppeld           De ketens tussen de zichtjaren lopen via tifs (#824). Zonder deze schakelaar
                            trekt de export van 2120 alle zichtjaren vanaf 2040 in een proces mee, want
                            de cumulatieve indicatoren (contante waarden, koolstof, methaan, sterfte,
                            SOMERS) lezen het vorige zichtjaar; elke tabel is dan een run van drie
                            kwartier. Met de schakelaar draait het script eerst per variant de zichtjaren
                            voor het exportzichtjaar, elk in een eigen proces: het item Zichtjaren/<jaar>/
                            Tijdreeks schrijft de ketentifs (Indicatoren/<casus>/Ketens) en de kaarten
                            van de tijdreeks. De export van het exportzichtjaar leest dan de ketens van
                            zijn voorganger en rekent alleen zichzelf. Voor elk zichtjaar toetst het
                            script of de ketentifs van de voorganger er staan, en erna of het zijn eigen
                            ketentifs heeft geschreven. Geen fingerprint: een bestaande tif wordt gelezen.
      -AlleenExportZichtjaar  Met -Ontkoppeld: de reeks overslaan en alleen het exportzichtjaar draaien,
                            op de ketentifs van een eerdere run. Het script eist dat die er staan en
                            waarschuwt als ze ouder zijn dan de stand van dat zichtjaar, want dan is de
                            allocatie opnieuw gedaan en hoort de reeks ook opnieuw. -AlleenLandschapstabellen
                            slaat de reeks ook over.
      -TabellenUitExport    De tabellen lezen de kaarten terug die de export van hetzelfde zichtjaar heeft
                            geschreven (#824), via ModelParameters/TabellenUitExport. De export gaat dan in
                            twee processen: eerst generates/Generate_Kaarten met de schakelaar uit, daarna
                            generates/Themas/Tabellen met de schakelaar aan. Elke volgende regio draait alleen
                            generates/Indicatoren_PerIndeling met de schakelaar aan, en met
                            -AlleenLandschapstabellen doen alle regio's dat. Een tabelstap eist dat de kaarten
                            van dat zichtjaar er staan: een ontbrekende tif geeft een [E]-regel in het log en
                            de stap valt om. De bereikbaarheid van groen rekent per regio opnieuw, op
                            teruggelezen invoer; alleen de landelijke tabel leest de groenkaarten zelf terug.
      -GeenToets            Slaat de toets op de invoer over. Alleen voor wie precies weet wat er staat.

   B. Omgevingsvariabelen die dit script zelf zet: StandAllocatieOntkoppeld=TRUE (stand uit de tifs),
      VariantDataOntkoppeld=TRUE, IndicatorenOntkoppeld (TRUE met -Ontkoppeld, anders FALSE),
      TabellenUitExport (per stap: TRUE alleen voor de tabelstappen van -TabellenUitExport),
      IndicatorRegio en ExportZichtjaar. LocalDataProjDir wordt gewist, GeoDMS leidt het pad af uit
      LocalDataDir plus de mapnaam boven cfg.

   C. Wat dit script NIET regelt en je vooraf moet nalopen:
      - De stand moet er staan voor ELK zichtjaar tot en met het exportzichtjaar, want cumulatieve
        indicatoren (contante waarden, koolstof, sterfte) rekenen alle voorgaande zichtjaren mee,
        in een proces (zonder -Ontkoppeld) of zichtjaar voor zichtjaar (met).
      - De basisdata van WriteBasedata/Generate_Run3 en Generate_Run4_IndicatorenData en de
        variantdata van WriteVariantData. Run2120.ps1 maakt ze allemaal; de toets hieronder meldt
        wat ontbreekt en welk item het maakt.
      - De legenda's (Export/Legendas/Schrijf) schrijft dit script zelf, ze zijn casusonafhankelijk.
      - De schakelaars in cfg\main\ModelParameters.dms, zie blok B van Run2120.ps1.

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
    [ValidateSet('NL','Provincie','COROP','Gemeente','NVM','Landschappen',
                 'Landschap_Kust','Landschap_Rivieren','Landschap_Veen','Landschap_Zand')]
    [string]   $IndicatorRegio = 'NL',
    [switch]   $Gebundeld,
    [switch]   $AlleenLandschapstabellen,
    [switch]   $Ontkoppeld,
    [switch]   $AlleenExportZichtjaar,
    [switch]   $TabellenUitExport,
    [switch]   $GeenToets
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Exe)) { throw "GeoDmsRun niet gevonden: $Exe" }
if (-not (Test-Path $Cfg)) { throw "Configuratie niet gevonden: $Cfg" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

$env:StandAllocatieOntkoppeld = 'TRUE'
$env:VariantDataOntkoppeld    = 'TRUE'
$env:IndicatorRegio           = $IndicatorRegio
$env:IndicatorenOntkoppeld    = if ($Ontkoppeld) { 'TRUE' } else { 'FALSE' }
$env:TabellenUitExport        = 'FALSE'
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

function Get-KetenNamen {
    # De namen van de ketentifs, gelezen uit de schrijfkant in Ketens.dms zodat dit script niet
    # achterloopt als daar een keten bijkomt: elke StorageName daar is Pad+'<naam>'+Staart.
    $dms = Join-Path (Split-Path $Cfg -Parent) 'main\Templates\Indicatoren\Ketens.dms'
    if (-not (Test-Path $dms)) { throw "Ketens.dms niet gevonden naast $Cfg" }
    $namen = @([regex]::Matches((Get-Content $dms -Raw), "StorageName\s*=\s*`"=Pad\+'([^']+)'\+Staart`"") | ForEach-Object { $_.Groups[1].Value })
    if ($namen.Count -eq 0) { throw "Geen ketentifs gevonden in $dms" }
    return $namen
}

function Assert-Ketens([string]$casus, [string]$jaar, [string]$standVan) {
    # Staan de ketentifs van dit zichtjaar er, en zijn ze jonger dan de stand van dat zichtjaar? Het
    # eerste is een eis, het tweede een waarschuwing: een oudere keten betekent dat de allocatie na
    # de vorige reeks opnieuw is gedaan.
    $map = Join-Path $LocalData "Indicatoren\$casus\Ketens"
    $mis = @(); $oud = @()
    $stand = Get-ChildItem (Join-Path $LocalData "Allocatie\$standVan\Stand$jaar\OP_rel_*.tif") -ErrorAction SilentlyContinue | Select-Object -First 1
    $namen = Get-KetenNamen
    foreach ($n in $namen) {
        $tif = Get-ChildItem (Join-Path $map "${n}_${jaar}_*.tif") -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $tif) { $mis += $n; continue }
        if ($stand -and $tif.LastWriteTime -lt $stand.LastWriteTime) { $oud += $n }
    }
    if ($mis.Count -gt 0) {
        throw "Ketentifs van $casus $jaar ontbreken in $map ($($mis.Count) van $($namen.Count)): $($mis -join ', '). Maak ze met een run zonder -AlleenExportZichtjaar, of los met /Indicatoren/$casus/Zichtjaren/$jaar/Tijdreeks en IndicatorenOntkoppeld=TRUE."
    }
    if ($oud.Count -gt 0) {
        Write-Regel "LET OP    : $($oud.Count) ketentifs van $casus $jaar zijn ouder dan de stand van $jaar ($($stand.LastWriteTime.ToString('s'))); is de allocatie opnieuw gedaan, draai dan de reeks opnieuw"
    }
}

$totaal = [Diagnostics.Stopwatch]::StartNew()
Write-Regel "config    : $Cfg"
Write-Regel "localdata : $LocalData"
Write-Regel "varianten : $($Varianten -join ', ')"
Write-Regel "zichtjaren: $($Zichtjaren -join ', ')"
Write-Regel "regio     : $IndicatorRegio$(if ($IndicatorRegio -eq 'Landschappen') { ', de vier landschapsgebieden van #760 na elkaar' })"
Write-Regel "ketens    : $(if ($Ontkoppeld) { 'ontkoppeld, via tifs per zichtjaar (#824)' } else { 'in een proces, elke export rekent alle voorgaande zichtjaren mee' })"
Write-Regel "tabellen  : $(if ($TabellenUitExport) { 'uit de geschreven kaarten, in een eigen proces na de kaarten (#824)' } else { 'levend, in hetzelfde proces als de kaarten' })"

$alleJaren = Get-Zichtjaren
$leen      = Get-VariantKolom $Cfg 'StandVanVariant'
function Get-StandVan([string]$v) { if ($leen[$v]) { $leen[$v] } else { $v } }
foreach ($y in $Zichtjaren) { if ($alleJaren.IndexOf($y) -lt 0) { throw "Zichtjaar $y staat niet in de configuratie ($($alleJaren -join ', '))" } }
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

# De regio's om te draaien: Landschappen is de vier aangeleverde gebieden van #760 na elkaar, een
# proces per gebied, want IndicatorRegio geldt per proces voor alle indicatoren tegelijk. De eerste
# regio draagt de volledige export; elke volgende alleen de regionale tabel, want de grids, de
# landelijke tabel en de claimrealisatie hangen niet van de indeling af. Met -AlleenLandschapstabellen
# ook de eerste alleen de tabel.
# De @( ) eromheen is nodig: een if-statement geeft zijn uitkomst als reeks terug, en een lijst van
# een element komt daar als kale string uit, zodat $regios[0] de eerste LETTER van de regionaam is.
$regios = @(if ($IndicatorRegio -eq 'Landschappen') { @('Landschap_Kust','Landschap_Rivieren','Landschap_Veen','Landschap_Zand') } else { $IndicatorRegio })

# Ontkoppeld (#824): eerst de reeks zichtjaren voor het laatste exportzichtjaar, elk in een eigen
# proces, in volgorde. Zichtjaren/<jaar>/Tijdreeks schrijft de ketentifs van dat jaar en de kaarten
# van de tijdreeks; het volgende zichtjaar leest die ketentifs via Ketens/Lees. Het eerste zichtjaar
# heeft geen voorganger en leest het basisjaar, net als zonder de schakelaar. Een ontbrekende
# ketentif geeft GeoDmsRun exit 0 met een gdal-waarschuwing, vandaar de toets voor en na elk jaar.
if ($Ontkoppeld) {
    $laatste = ($Zichtjaren | ForEach-Object { $alleJaren.IndexOf($_) } | Measure-Object -Maximum).Maximum
    $reeks   = @(if ($laatste -gt 0) { $alleJaren[0..($laatste - 1)] } else { @() })
    if ($reeks.Count -eq 0) {
        Write-Regel "reeks     : geen, $($alleJaren[$laatste]) is het eerste zichtjaar"
    } elseif ($AlleenExportZichtjaar -or $AlleenLandschapstabellen) {
        Write-Regel "reeks     : overgeslagen; de ketentifs van $($reeks[-1]) moeten er staan"
    } elseif ($Gebundeld) {
        Write-Regel "reeks     : $($reeks -join ', '), per zichtjaar een proces voor $($Varianten.Count) varianten"
        for ($i = 0; $i -lt $reeks.Count; $i++) {
            $j = $reeks[$i]
            if ($i -gt 0) { foreach ($v in $Varianten) { Assert-Ketens "${Scenario}_$v" $reeks[$i - 1] "${Scenario}_$(Get-StandVan $v)" } }
            $env:ExportZichtjaar = $j
            Invoke-Export "reeks-gebundeld-$j" @($Varianten | ForEach-Object { "/Indicatoren/${Scenario}_$_/Zichtjaren/$j/Tijdreeks" })
            foreach ($v in $Varianten) { Assert-Ketens "${Scenario}_$v" $j "${Scenario}_$(Get-StandVan $v)" }
        }
    } else {
        Write-Regel "reeks     : $($reeks -join ', '), per variant en zichtjaar een proces"
        foreach ($v in $Varianten) {
            for ($i = 0; $i -lt $reeks.Count; $i++) {
                $j = $reeks[$i]
                if ($i -gt 0) { Assert-Ketens "${Scenario}_$v" $reeks[$i - 1] "${Scenario}_$(Get-StandVan $v)" }
                $env:ExportZichtjaar = $j
                Invoke-Export "reeks-$v-$j" @("/Indicatoren/${Scenario}_$v/Zichtjaren/$j/Tijdreeks")
                Assert-Ketens "${Scenario}_$v" $j "${Scenario}_$(Get-StandVan $v)"
            }
        }
    }
}

# De export zelf. Ontkoppeld leest het exportzichtjaar de ketentifs van zijn voorganger, dus die
# worden eerst getoetst; zonder de schakelaar rekent de export de hele reeks in het proces mee.
function Assert-Voorganger([string]$v, [string]$y) {
    if (-not $Ontkoppeld) { return }
    $i = $alleJaren.IndexOf($y)
    if ($i -gt 0) { Assert-Ketens "${Scenario}_$v" $alleJaren[$i - 1] "${Scenario}_$(Get-StandVan $v)" }
}
for ($r = 0; $r -lt $regios.Count; $r++) {
    $regio = $regios[$r]
    $env:IndicatorRegio = $regio
    $alleenTabel = $AlleenLandschapstabellen -or ($r -gt 0)
    # De stappen voor deze regio. Zonder -TabellenUitExport is dat een aanroep: de volledige export, of
    # alleen de regionale tabel. Met de schakelaar gaat de volledige export in twee processen (#824): eerst
    # alle kaarten met TabellenUitExport uit, dan de tabellen met de schakelaar aan. Een lezer kent zijn
    # schrijver niet, dus in een proces zou een tabel een tif kunnen openen voordat hij geschreven is.
    $stappen = @()
    if (-not $TabellenUitExport) {
        $wat  = if ($alleenTabel) { 'Zichtjaren/Export/generates/Indicatoren_PerIndeling' } else { 'Zichtjaren/Export/Generate_Indicatoren' }
        $naam = if ($alleenTabel) { "tabel-$regio" } else { "indicatoren-$regio" }
        $stappen += [pscustomobject]@{ Wat = $wat; UitExport = 'FALSE'; Naam = $naam }
    } elseif ($alleenTabel) {
        $stappen += [pscustomobject]@{ Wat = 'Zichtjaren/Export/generates/Indicatoren_PerIndeling'; UitExport = 'TRUE'; Naam = "tabel-$regio" }
    } else {
        $stappen += [pscustomobject]@{ Wat = 'Zichtjaren/Export/generates/Generate_Kaarten'; UitExport = 'FALSE'; Naam = "kaarten-$regio" }
        $stappen += [pscustomobject]@{ Wat = 'Zichtjaren/Export/generates/Themas/Tabellen';  UitExport = 'TRUE';  Naam = "tabellen-$regio" }
    }
    foreach ($stap in $stappen) {
        $env:TabellenUitExport = $stap.UitExport
        if ($Gebundeld) {
            Write-Regel "modus     : gebundeld, per zichtjaar een proces voor $($Varianten.Count) varianten ($($stap.Naam))"
            foreach ($y in $Zichtjaren) {
                foreach ($v in $Varianten) { Assert-Voorganger $v $y }
                $env:ExportZichtjaar = $y
                $items = @($Varianten | ForEach-Object { "/Indicatoren/${Scenario}_$_/$($stap.Wat)" })
                Invoke-Export "$($stap.Naam)-gebundeld-$y" $items
            }
        } else {
            foreach ($v in $Varianten) {
                foreach ($y in $Zichtjaren) {
                    Assert-Voorganger $v $y
                    $env:ExportZichtjaar = $y
                    Invoke-Export "$($stap.Naam)-$v-$y" @("/Indicatoren/${Scenario}_$v/$($stap.Wat)")
                }
            }
        }
    }
    $env:TabellenUitExport = 'FALSE'
}

$totaal.Stop()
Write-Regel "ALLE INDICATOREN KLAAR in $([math]::Round($totaal.Elapsed.TotalHours,2)) uur"
Write-Regel "volgende  : batch\MaakOplevering.ps1 -Doel <opleveringsmap> -Issue <nummer>"
