<#
================================================================================================
 Run2120.ps1: de productierun van RSopen NL2120, van de basisdata tot en met zichtjaar 2120
================================================================================================

 WAT DIT SCRIPT DOET
   1. Schrijft de ontkoppelde basisdata weg (WriteBasedata, vier stappen).
   2. Schrijft per variant de variantdata weg (opbrengsten per ontwikkelpakket, opbrengstderving).
   3. Alloceert per variant elk zichtjaar in een eigen GeoDmsRun-proces, dat de stand van het
      vorige zichtjaar uit de tifs leest. Daardoor blijft het geheugen per proces beperkt en is
      een afgebroken reeks te hervatten bij het zichtjaar waar hij bleef steken.
   De indicatoren zijn een aparte stap: batch\RunIndicatoren.ps1.

 HOE START JE HET (vanuit een PowerShell-venster in de map batch)
   Volledige reeks, alles opnieuw, twee varianten:
       .\Run2120.ps1 -Varianten BAU,NbSGenuanceerd
   Basisdata en variantdata staan er al, alleen alloceren:
       .\Run2120.ps1 -Varianten BAU -SkipBasedata -SkipVariantData
   Hervatten na een fout, bij een stap uit status.tsv (de naam staat in de kolom stap):
       .\Run2120.ps1 -Varianten BAU -SkipBasedata -SkipVariantData -StartBij allocatie-BAU-Y2070
   Landbouwronde over bestaande standen (BAU2 na BAU, met de stedelijke stand overgenomen):
       .\Run2120.ps1 -Varianten BAU2 -SkipBasedata -AlleenLandbouw
   Het script stopt bij de eerste stap die misgaat en zegt welke. Elke stap heeft een eigen log
   in de logmap en een regel in status.tsv.

 INSTELLINGEN, IN DRIE SOORTEN

   A. Parameters van dit script. Geef ze mee op de commandoregel; wat je niet meegeeft krijgt
      de standaardwaarde uit het blok param() hieronder.
      -Exe            GeoDmsRun.exe van de geinstalleerde GeoDMS. Niet de build uit Visual Studio:
                      die wordt opnieuw gecompileerd terwijl een reeks loopt.
      -Cfg            De configuratie, cfg\main.dms van de werkkopie waarmee je rekent.
      -LocalData      Waar de uitvoer staat. Standaard C:\LocalData\<naam van de werkkopie>; het script
                      zet de omgevingsvariabele LocalDataProjDir bewust NIET, GeoDMS leidt dit pad
                      zelf af uit de registersleutel LocalDataDir plus de mapnaam boven cfg.
      -Scenario       Het WLO-scenario, standaard WLO_hoog. Casusnamen worden <scenario>_<variant>.
      -Varianten      Welke varianten, als lijst: -Varianten BAU,BAU2,NbSGenuanceerd. De namen
                      staan in cfg\main\VariantParameters\VariantK.dms, kolom name.
      -Zichtjaren     Leeg laten: het script leest ze uit de configuratie (Model_FirstZichtjaar tot
                      Model_FinalYear). Alleen vullen om een deel te draaien, bijvoorbeeld Y2040,Y2050.
      -SkipBasedata   Basisdata niet opnieuw wegschrijven. Het script controleert dan wel of de
                      bestanden er staan en zegt welke stap ze maakt als er iets ontbreekt.
      -SkipVariantData  Idem voor de variantdata.
      -StartBij       Naam van de stap waar de reeks verdergaat; alles ervoor wordt overgeslagen.
      -HerbouwBasedata  Bevestigt dat je de basisdata opnieuw maakt terwijl er al standen staan.
                      Zonder deze schakelaar weigert het script dat, omdat vroege en late zichtjaren
                      dan met verschillende invoer zouden rekenen.
      -AlleenLandbouw Bevestigt dat alleen de landbouw alloceert. Hoort samen met de schakelaar
                      OntkoppelStedelijkeKlasses op TRUE (zie B); het script toetst dat.
      -DiagnoseNaZichtjaar  Na welke zichtjaren het diagnoseharnas meedraait (ongeveer acht
                      minuten per zichtjaar per variant). Leeg is nooit.

   B. Schakelaars in de configuratie die dit script NIET zet maar waar de run wel van afhangt.
      Loop ze na voordat je start; ze staan in cfg\main\ModelParameters.dms tenzij anders vermeld.
      OntkoppelStedelijkeKlasses   FALSE voor een volle reeks. TRUE laat alleen de landbouw
                                   alloceren en neemt wonen en werken uit bestaande standtifs.
      ExotenActief                 (ModelParameters\Landbouw.dms) Of de exotische gewassen meedoen.
      AlleenEindjaar               Alleen voor debuggen; in een productierun FALSE.
      SectorAllocRegio             De tabel met sectoren die alloceren. Een sector aan- of
                                   uitzetten verandert het SS-nummer in alle bestandsnamen, en
                                   daarmee zijn bestaande standen onbruikbaar.
      VariantK/StandVanVariant     (VariantParameters\VariantK.dms) Een variant die hier een andere
                                   naam draagt, leent die stand en alloceert niet.
      Model_FirstZichtjaar, Model_FinalYear   De reeks zichtjaren.
      ConfigSettings.dms           Machine-eigen paden (bronnen, LocalData). Staat niet in git;
                                   elke machine heeft zijn eigen exemplaar.

   C. Omgevingsvariabelen die dit script zelf zet, zodat de run niet afhangt van wat er in een
      venster toevallig staat: StandAllocatieOntkoppeld=TRUE en VariantDataOntkoppeld=TRUE.
      LocalDataProjDir wordt juist gewist, zie -LocalData.

 ALS HET MISGAAT
   Kijk in status.tsv (kolom exit) en in het log van de stap; regels met [E] zijn de fouten.
   Exit 2 is een fout in de configuratie (parse), exit 1 een rekenfout of een ontbrekend bestand.
   Een stap kan met exit 0 eindigen en toch een [E]-regel hebben; het script telt die ook.
   Ontbreekt er basisdata, dan zegt het script welke WriteBasedata-stap die maakt.
   Draai nooit twee GeoDmsRun-processen tegelijk op dezelfde LocalData: ze botsen op bestanden
   die ze allebei openen, en het log zegt dan "being used by another process" of blijft stil.
================================================================================================
#>
[CmdletBinding()]
param(
    [string]   $Exe        = 'C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe',
    [string]   $Cfg        = 'C:\ProjDir\RSopen_NL2120_productie\cfg\main.dms',
    [string]   $LocalData  = 'C:\LocalData\RSopen_NL2120_productie',
    [string]   $LogDir     = 'C:\ProjDir\RSopen_NL2120_productie\batch\log\run2120',
    [string]   $Scenario   = 'WLO_hoog',
    [string[]] $Varianten  = @('BAU','BAU2'),
    [string[]] $Zichtjaren = @(),
    [string[]] $DiagnoseNaZichtjaar = @(),
    [switch]   $SkipBasedata,
    [switch]   $SkipVariantData,
    [string]   $StartBij   = '',
    [switch]   $HerbouwBasedata,
    [switch]   $AlleenLandbouw
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Exe)) { throw "GeoDmsRun niet gevonden: $Exe" }
if (-not (Test-Path $Cfg)) { throw "Configuratie niet gevonden: $Cfg" }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

# Batchinstellingen. Deze overrulen de defaults in ModelParameters.dms.
$env:StandAllocatieOntkoppeld = 'TRUE'
$env:VariantDataOntkoppeld    = 'TRUE'
# Nadrukkelijk niet zetten, zie -LocalData in de toelichting bovenaan.
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
    # NietFataal is voor stappen die meten en niets produceren waar een latere stap op leunt.
    # Een omvallende meting hoort een reeks van zeventien uur niet te stoppen: de allocatie van het
    # volgende zichtjaar hangt van de stand af en niet van de diagnose-uitdraai. De stap wordt wel
    # als mislukt in status.tsv gezet en op het scherm gemeld, zodat er achteraf geen stilte staat
    # waar een meting hoorde te staan.
    param([string]$Stap, [string]$Item, [switch]$NietFataal)

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
        if ($NietFataal) {
            Write-Regel "doorgaan  : $Stap was een meting, dus de reeks loopt door. Dit zichtjaar mist zijn uitdraai."
            return
        }
        throw "Stap '$Stap' mislukt: $reden"
    }

    Write-Regel "klaar     : $Stap ($([math]::Round($sec/60,1)) min)"
}

function Get-Zichtjaren {
    # Haalt de zichtjaren uit de configuratie in plaats van ze hier te herhalen. Zie de memory-notitie
    # over RunZichtjaren.cmd, dat jaartallen bij naam noemde en daardoor stil een zichtjaar oversloeg.
    # Let op: vast logpad, geen tijdstempel. GeoDmsRun leegt een bestaand logbestand niet, dus dit
    # bestand groeit bij elke aanroep. Onschadelijk zolang deze functie de stdout leest en de
    # exitcode toetst; wie hier ooit een grep op [E] aan toevoegt vindt ook de fouten van vorige
    # runs. Zet er dan eerst een tijdstempel in, zoals Invoke-Stap hierboven doet.
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

function Get-VariantKolom([string]$CfgPad, [string]$Kolom) {
    # Leest een kolom uit VariantK.dms als tabel variant -> waarde. Bewust een parse van de
    # configuratie en geen GeoDmsRun: dit moet klaar zijn voordat de eerste stap begint, en het
    # kost zo milliseconden in plaats van een minuut.
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

function Test-Invoer {
    # De toets uit ObjectVision/RSopen#816: zeg VOORAF welke ontkoppelde bestanden ontbreken en welke stap
    # ze maakt, in plaats van na een uur rekenen om te vallen op 'Unknown identifier' of 'cannot open
    # dataset'. Op 2026-09-10 kostte dat twee valse starts: de proxies van WriteBasedata/Generate_Run3
    # ontbraken (103 s), en daarna de opbrengstderving (2357 s). De lijst is een ondergrens: een
    # representatief bestand per stap, geen volledige inventaris.
    param([string]$Fase)   # 'allocatie' of 'variantdata'

    $eisen = @()
    $eisen += ,@('BaseData\Vastgoed\VolledigeTabel_*\WP5\*.mmd',        'WP5-pandtypering',            '/WriteBasedata/Generate_Run1')
    $eisen += ,@('BaseData\Grondgebruik\BBG\BBG*_25m_Modus_*.tif',      'BBG-vergridding',             '/WriteBasedata/Generate_Run2')
    $eisen += ,@('BaseData\Vastgoed\Verwervingskosten_Woningen_*.tif',  'verwervingskosten',           '/WriteBasedata/Generate_Run2')
    $eisen += ,@('BaseData\Grondgebruik\NBP\*.tif',                     'beheertypenkaart basisjaar',  '/WriteBasedata/Generate_Run2')
    $eisen += ,@('BaseData\Grondgebruik\MNP\*.tif',                     'MNP-planpotentieel',          '/WriteBasedata/Generate_Run2')
    if ($Fase -eq 'allocatie') {
        $eisen += ,@('BaseData\StandBasisjaar\Wonen\*.tif',             'stand basisjaar',             '/WriteBasedata/Generate_Run3')
        $eisen += ,@('BaseData\Vastgoed\WP2xVSSH_Proxy\*',              'woningsubsector-proxies',     '/WriteBasedata/Generate_Run3')
        $eisen += ,@('BaseData\Vastgoed\Sloopkosten_Woningen_*.tif',    'sloopkosten',                 '/WriteBasedata/Generate_Run3')
        $eisen += ,@('BaseData\Suitabilities\Werken_raw_*.tif',         'werken-geschiktheid',         '/WriteBasedata/Generate_Run3')
        $eisen += ,@('BaseData\Suitabilities\Waterberging\Depth_Norm_*.tif', 'waterbergingsnormen',    '/WriteBasedata/Generate_Run3')
        $hydro  = Get-VariantKolom $Cfg 'Hydrologie_Levering'
        $opbr   = Get-VariantKolom $Cfg 'OpbrengstenVariant_Wonen'
        foreach ($v in $Varianten) {
            if (-not $opbr.ContainsKey($v)) { throw "Variant $v staat niet in VariantK.dms (kolom name); bekende varianten: $($opbr.Keys -join ', ')" }
            $eisen += ,@("BaseData\Landbouw\WWL_Opbrengstderving\$($hydro[$v])_*.tif", "opbrengstderving van levering $($hydro[$v]) (variant $v)", "/WriteVariantData/per_Variant/$v/Generate_Run2")
            $eisen += ,@("VariantData\Vastgoed\Opbrengsten_perOP\$($opbr[$v])\*.tif", "opbrengsten per pakket, set $($opbr[$v]) (variant $v)", "/WriteVariantData/per_Variant/$v/Generate_Run1")
            $eisen += ,@("VariantData\Grondgebruik\BGT\EvidentBenut_*_$v.tif",         "evident benut (variant $v)",                     "/WriteVariantData/per_Variant/$v/Generate_Run1")
        }
    }

    $mis = @()
    foreach ($e in $eisen) {
        $pad = Join-Path $LocalData $e[0]
        if (-not (Get-ChildItem $pad -ErrorAction SilentlyContinue | Select-Object -First 1)) { $mis += $e }
    }
    if ($mis.Count -gt 0) {
        Write-Regel "GESTOPT: ontkoppelde invoer ontbreekt in $LocalData. Maak hem eerst met GeoDmsRun op het genoemde item:"
        foreach ($m in $mis) { Write-Host ("   {0,-55} {1,-45} {2}" -f $m[0], $m[1], $m[2]) }
        throw "Invoer voor fase $Fase ontbreekt"
    }
    Write-Regel "controle  : ontkoppelde invoer voor fase $Fase aanwezig ($($eisen.Count) toetsen)"
}

function Test-StedelijkeKlassen {
    # ModelParameters/OntkoppelStedelijkeKlasses is een debugschakelaar zonder omgevingsvariabele: hij
    # staat in de configuratie en Run2120 zet hem niet. Op TRUE slaat elke niet-landbouwregel in
    # SectorAllocRegio zijn allocatie over en geeft hij zijn ingangsstand door, en leest de landbouw
    # de stand van datzelfde zichtjaar van schijf. Dat is de bedoelde route voor een landbouwronde
    # bovenop bestaande standtifs, maar in een volle reeks levert het stedelijke standen op die niet
    # zijn gealloceerd. Niets in het log zegt dat: de NoAlloc-tak is gratis en geeft geen foutregel.
    # Vandaar deze toets, die de schakelaar en de bedoeling van de aanroeper naast elkaar legt.
    $mp = Join-Path (Split-Path $Cfg -Parent) 'main\ModelParameters.dms'
    if (-not (Test-Path $mp)) { throw "ModelParameters.dms niet gevonden naast $Cfg" }
    $m = [regex]::Match((Get-Content $mp -Raw), 'OntkoppelStedelijkeKlasses\s*:=\s*(TRUE|FALSE)')
    if (-not $m.Success) { throw "OntkoppelStedelijkeKlasses niet gevonden in $mp" }
    $ontkoppeld = ($m.Groups[1].Value -eq 'TRUE')

    if ($ontkoppeld -and -not $AlleenLandbouw) {
        Write-Regel "GESTOPT: OntkoppelStedelijkeKlasses staat op TRUE, dus alleen Landbouw alloceert."
        Write-Regel "Zet hem op FALSE in $mp voor een volle reeks, of geef -AlleenLandbouw mee als dat de bedoeling is."
        throw 'OntkoppelStedelijkeKlasses staat op TRUE zonder -AlleenLandbouw'
    }
    if (-not $ontkoppeld -and $AlleenLandbouw) {
        Write-Regel "GESTOPT: -AlleenLandbouw gegeven, maar OntkoppelStedelijkeKlasses staat op FALSE."
        Write-Regel "Zo alloceert de reeks alsnog alle sectoren. Zet de schakelaar op TRUE in $mp."
        throw '-AlleenLandbouw zonder OntkoppelStedelijkeKlasses op TRUE'
    }
    $wat = if ($ontkoppeld) { 'alleen Landbouw, stedelijke stand uit de bestaande tifs' } else { 'alle sectoren uit SectorAllocRegio' }
    Write-Regel "controle  : OntkoppelStedelijkeKlasses is $($m.Groups[1].Value), dus $wat"
}

function Show-Schakelaars {
    # De schakelaars uit blok B van de toelichting, zoals ze nu in de configuratie staan. Geen toets,
    # alleen tonen: wie de run start ziet dan meteen waarmee hij rekent, en het staat in het scherm-
    # log van de aanroep.
    $mpDir = Join-Path (Split-Path $Cfg -Parent) 'main'
    $bron = @{
        'AlleenEindjaar'       = 'ModelParameters.dms'
        'Model_FirstZichtjaar' = 'ModelParameters.dms'
        'Model_FinalYear'      = 'ModelParameters.dms'
        'ExotenActief'         = 'ModelParameters\Landbouw.dms'
    }
    foreach ($naam in @('Model_FirstZichtjaar','Model_FinalYear','AlleenEindjaar','ExotenActief')) {
        $tekst = Get-Content (Join-Path $mpDir $bron[$naam]) -Raw
        $m = [regex]::Match($tekst, "$naam\s*:=\s*=?\s*([^,;\r\n]+)")
        $w = if ($m.Success) { $m.Groups[1].Value.Trim() } else { '(niet gevonden)' }
        Write-Regel ("schakelaar: {0,-22} {1}   ({2})" -f $naam, $w, $bron[$naam])
    }
}

Write-Regel "build     : $(Split-Path (Split-Path $Exe -Parent) -Leaf)"
Write-Regel "config    : $Cfg"
Write-Regel "localdata : $LocalData"
Write-Regel "varianten : $($Varianten -join ', ')"

Show-Schakelaars
Test-StedelijkeKlassen

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
    # Vier stappen, in deze volgorde. Run3 (stand basisjaar, proxies, sloopkosten, werken-geschiktheid,
    # normen, kernels) is nodig voor de allocatie en stond tot 11 september 2026 niet in dit script;
    # de allocatie viel dan na een uur om op 'Unknown identifier meergezins_VrijeSector_Proxy'.
    # Run4 (BGT-capaciteiten) is alleen voor de indicatoren, maar hoort bij een verse LocalData en
    # kost ruim een uur; wie hem overslaat krijgt hem bij RunIndicatoren.ps1 alsnog voorgeschoteld.
    Invoke-Stap 'basedata-run1' '/WriteBasedata/Generate_Run1'
    Invoke-Stap 'basedata-run2' '/WriteBasedata/Generate_Run2'
    Invoke-Stap 'basedata-run3' '/WriteBasedata/Generate_Run3'
    Invoke-Stap 'basedata-run4' '/WriteBasedata/Generate_Run4_IndicatorenData'
    Test-Dictionaries
} else {
    Test-Invoer 'basedata'
}

if (-not $SkipVariantData) {
    Test-ReeksNogNietBegonnen 'variantdata opnieuw wegschrijven'
    foreach ($v in $Varianten) {
        Invoke-Stap "variantdata-$v-run1" "/WriteVariantData/per_Variant/$v/Generate_Run1"
        Invoke-Stap "variantdata-$v-run2" "/WriteVariantData/per_Variant/$v/Generate_Run2"
    }
}

# Alles wat de allocatie leest hoort er nu te staan, hoe de fases hierboven ook zijn gelopen.
Test-Invoer 'allocatie'

function Test-LeenAanname([string]$CfgPad, [string]$Lener, [string]$Uitlener) {
    # De aanname onder het lenen is dat de twee varianten op alles wat de allocatie raakt gelijk zijn.
    # Deze toets keert dat om: hij eist dat de kolommen waarop ze verschillen precies de bekende zijn.
    # Dat vangt het echte risico af, namelijk dat er ooit een zesde afwijkende rij bij komt.
    $vk = Join-Path (Split-Path $CfgPad -Parent) 'main\VariantParameters\VariantK.dms'
    $tekst = Get-Content $vk -Raw
    $toegestaan = @('name','StandVanVariant','LeentStand','Label',
                    'WinterdroogleggingK_ref','ZomerdroogleggingK_ref',
                    'InfiltratieMaatregelK_ref','WaterbergingClaimBron')
    $namen = @([regex]::Matches([regex]::Match($tekst,"attribute<[^>]+>\s+name\s*:\s*\[(.*?)\]",'Singleline').Groups[1].Value, "'([^']*)'") | ForEach-Object { $_.Groups[1].Value })
    $iL = $namen.IndexOf($Lener); $iU = $namen.IndexOf($Uitlener)
    if ($iL -lt 0 -or $iU -lt 0) { throw "variant $Lener of $Uitlener staat niet in VariantK" }

    $afwijkend = @()
    foreach ($m in [regex]::Matches($tekst, "attribute<[^>]+>\s+(\w+)\s*:\s*\[(.*?)\]", 'Singleline')) {
        $kol = $m.Groups[1].Value
        if ($toegestaan -contains $kol) { continue }
        $w = @([regex]::Matches($m.Groups[2].Value, "'([^']*)'") | ForEach-Object { $_.Groups[1].Value })
        if ($w.Count -eq 0) { $w = @($m.Groups[2].Value -split ',' | ForEach-Object { $_.Trim() }) }
        if ($w.Count -le [Math]::Max($iL,$iU)) { continue }
        if ($w[$iL] -ne $w[$iU]) { $afwijkend += "$kol ($($w[$iU]) tegen $($w[$iL]))" }
    }
    if ($afwijkend.Count -gt 0) {
        Write-Regel "GESTOPT: $Lener leent de stand van $Uitlener, maar ze verschillen op kolommen die de allocatie kunnen raken:"
        $afwijkend | ForEach-Object { Write-Host "   $_" }
        throw "Leenaanname geschonden voor $Lener"
    }

    # Tweede voorwaarde, en die staat niet in VariantK: de gelijkheid rust erop dat de sector Landbouw
    # niet wordt gealloceerd. Die schakelaar zit in ModelParameters/SectorAllocRegio, dus geen enkele
    # kolomvergelijking ziet hem.
    $mp = Join-Path (Split-Path $CfgPad -Parent) 'main\ModelParameters.dms'
    $regels = (Get-Content $mp) | Where-Object { $_ -match "^\s*[,']" -and $_ -match "'Landbouw'" -and $_ -notmatch '^\s*//' }
    if ($regels) {
        Write-Regel "GESTOPT: $Lener leent de stand van $Uitlener, maar de sector Landbouw staat aan in SectorAllocRegio."
        $regels | ForEach-Object { Write-Host "   $($_.Trim())" }
        throw "Leenaanname geschonden: Landbouw wordt gealloceerd"
    }
    Write-Regel "leentoets  : $Lener mag de stand van $Uitlener lezen (geen afwijkende kolom, Landbouw uit)"
}


$leen = Get-VariantKolom $Cfg 'StandVanVariant'

foreach ($v in $Varianten) {
    $uitlener = $leen[$v]
    if ($uitlener -and $uitlener -ne $v) {
        # Deze variant leent haar stand van een andere en hoeft dus niet te alloceren. De
        # indicatorenkant leest de tifs van de uitlener via VariantK/StandVanVariant; zie
        # Templates/Indicatoren_T/StandCasus_name.
        Test-LeenAanname $Cfg $v $uitlener
        if (-not ($Varianten -contains $uitlener)) {
            throw "Variant $v leent de stand van $uitlener, maar die staat niet in -Varianten. Draai $uitlener mee of zet StandVanVariant terug."
        }
        Write-Regel "overslaan : allocatie-$v, leent de stand van $uitlener"
        continue
    }
    foreach ($y in $Zichtjaren) {
        Invoke-Stap "allocatie-$v-$y" "/Allocatie/${Scenario}_$v/Zichtjaren/$y/Impl/Generate"

        # Het diagnoseharnas achter de gekozen zichtjaren aan, zodat de uitkomst achteraf te
        # beoordelen is zonder opnieuw te rekenen. Wat er tijdens de run niet is weggeschreven
        # kun je naderhand niet meer nakijken; zie ObjectVision/RSopen#724.
        #
        # Kost ongeveer acht minuten per zichtjaar per variant. Draai hem daarom niet overal:
        # het eerste zichtjaar vangt een systematische fout na een uur in plaats van na zeven,
        # en het laatste is het zichtjaar dat wordt opgeleverd. Beoordelen doe je met
        # ToetsOplevering.ps1, die deze uitdraaien leest.
        if ($DiagnoseNaZichtjaar -contains $y) {
            $env:DiagCasus = "${Scenario}_$v"
            $env:DiagJaar  = "'$y'"
            Invoke-Stap "diagnose-$v-$y" '/Diagnose/GenerateAll' -NietFataal
        }
    }
}

$totaal.Stop()
Write-Regel "ALLES KLAAR in $([math]::Round($totaal.Elapsed.TotalHours,2)) uur"
Write-Regel "volgende  : batch\RunIndicatoren.ps1 -Varianten $($Varianten -join ',') -IndicatorRegio Landschap"
