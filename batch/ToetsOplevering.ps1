<#
.SYNOPSIS
    Beoordeelt na een productierun of de uitkomst opleverbaar is, zonder opnieuw te rekenen.

.DESCRIPTION
    Drie trappen, van gratis naar duur. Trap A en B kosten samen seconden en gebruiken alleen wat
    de run heeft weggeschreven; die kun je dus draaien terwijl de volgende variant nog loopt.
    Trap C rekent zelf en kost ongeveer twintig minuten per casus.

    De opzet gaat uit van de les van 31 augustus: wat er tijdens de run niet is weggeschreven kun je
    achteraf niet beoordelen zonder opnieuw te draaien. Zorg dus dat de run de diagnosestap per
    zichtjaar meeneemt, anders is trap B leeg. Zie de toelichting onderaan.

    Elke toets meldt PASS, FAIL of GEEN DATA. GEEN DATA is nadrukkelijk geen PASS.

.EXAMPLE
    .\ToetsOplevering.ps1 -LocalData C:\LocalData\RSopen_NL2120_productie -Varianten BAU,BAU2

.EXAMPLE
    .\ToetsOplevering.ps1 -TrapC -Varianten NbSGenuanceerd
#>
[CmdletBinding()]
param(
    [string]   $LocalData  = 'C:\LocalData\RSopen_NL2120_productie',
    [string]   $Cfg        = 'C:\ProjDir\RSopen_NL2120_productie\cfg\main.dms',
    [string]   $Exe        = 'C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe',
    [string]   $Scenario   = 'WLO_hoog',
    [string[]] $Varianten  = @('BAU','BAU2'),
    [string[]] $Zichtjaren = @(),
    # Alleen bestanden die na dit tijdstip zijn geschreven tellen als vers. Laat leeg om de
    # controle over te slaan; geef het starttijdstip van de run mee om verouderde uitdraaien
    # te ontmaskeren. Vorm: 'yyyy-MM-dd HH:mm'.
    [string]   $RunGestartOp = '',
    [switch]   $TrapC,
    [string]   $Rapport    = ''
)

$ErrorActionPreference = 'Continue'
if (-not $Rapport) { $Rapport = Join-Path $LocalData 'toets_oplevering.md' }
$vers = if ($RunGestartOp) { [datetime]::ParseExact($RunGestartOp, 'yyyy-MM-dd HH:mm', $null) } else { $null }

$script:Regels = @()
function Meld {
    param([string]$Trap, [string]$Casus, [string]$Toets, [string]$Oordeel, [string]$Gemeten, [string]$Verwacht)
    $script:Regels += [pscustomobject]@{ Trap=$Trap; Casus=$Casus; Toets=$Toets; Oordeel=$Oordeel; Gemeten=$Gemeten; Verwacht=$Verwacht }
    $kleur = switch ($Oordeel) { 'PASS' {'Green'} 'FAIL' {'Red'} default {'Yellow'} }
    Write-Host ("{0,-5} {1,-22} {2,-40} {3,-10} {4}" -f $Trap, $Casus, $Toets, $Oordeel, $Gemeten) -ForegroundColor $kleur
}

# Verwachte setgroottes per variant, uit de OP-tabel na #721.
$OPSetGrootte = @{ 'BAU'=27; 'BAU2'=27; 'NbSMax'=41; 'NbSGenuanceerd'=39 }
$AantalSubsectoren = 11

function Get-Zichtjaren([string]$casusPad) {
    Get-ChildItem $casusPad -Directory -Filter 'Stand Y*' -ErrorAction SilentlyContinue |
        ForEach-Object { $_.Name } | Sort-Object
}

# ---------------------------------------------------------------- trap A: wat er op schijf staat
function TrapA([string]$variant) {
    $casus = "${Scenario}_$variant"
    $pad   = Join-Path $LocalData "Allocatie\$casus"
    if (-not (Test-Path $pad)) { Meld 'A' $casus 'allocatiemap bestaat' 'FAIL' 'ontbreekt' $pad; return }

    $standen = Get-ChildItem $pad -Directory -Filter 'Stand*' -ErrorAction SilentlyContinue |
               Where-Object { $_.Name -notmatch 'vintage' } | Sort-Object Name
    if ($Zichtjaren.Count -gt 0) { $standen = $standen | Where-Object { $Zichtjaren -contains ($_.Name -replace '^Stand','') } }

    Meld 'A' $casus 'aantal zichtjaren met een stand' $(if ($standen.Count -gt 0) {'PASS'} else {'FAIL'}) "$($standen.Count)" 'minstens 1'

    foreach ($s in $standen) {
        $jaar = $s.Name -replace '^Stand',''

        # De blokkade van #721: zonder zijbestand weigert de leeskant deze stand en breekt het
        # volgende zichtjaar. Dit is de goedkoopste toets die er is en hij vangt de duurste fout.
        $params = @(Get-ChildItem $s.FullName -Filter '*.params.txt' -ErrorAction SilentlyContinue)
        if ($params.Count -eq 0) {
            Meld 'A' $casus "$jaar legenda-zijbestand" 'FAIL' 'ontbreekt' 'OP_rel...tif.params.txt'
        } else {
            $inhoud = Get-Content $params[0].FullName -Raw
            $nOP  = ((($inhoud -split 'op_set=')[1] -split ';')[0] -split ',').Count
            $nSub = ((($inhoud -split 'subsector_set=')[1]) -split ',').Count
            $okOP = ($OPSetGrootte.ContainsKey($variant) -and $nOP -eq $OPSetGrootte[$variant])
            Meld 'A' $casus "$jaar legenda, aantal pakketten" $(if ($okOP) {'PASS'} else {'FAIL'}) "$nOP" "$($OPSetGrootte[$variant])"
            Meld 'A' $casus "$jaar legenda, aantal subsectoren" $(if ($nSub -eq $AantalSubsectoren) {'PASS'} else {'FAIL'}) "$nSub" "$AantalSubsectoren"
        }

        # Een leeggeschreven tif is de klassieke uitkomst van twee runs op dezelfde LocalData.
        $tifs = @(Get-ChildItem $s.FullName -Recurse -Filter '*.tif' -ErrorAction SilentlyContinue)
        $leeg = @($tifs | Where-Object { $_.Length -lt 10240 })
        Meld 'A' $casus "$jaar tifs niet leeg" $(if ($leeg.Count -eq 0) {'PASS'} else {'FAIL'}) "$($tifs.Count) tifs, $($leeg.Count) onder 10 kB" '0 leeg'

        if ($vers) {
            $oud = @($tifs | Where-Object { $_.LastWriteTime -lt $vers })
            Meld 'A' $casus "$jaar stand is van deze run" $(if ($oud.Count -eq 0) {'PASS'} else {'FAIL'}) "$($oud.Count) bestanden ouder dan de runstart" '0'
        }
    }
}

# -------------------------------------------------- trap B: wat de diagnosestap heeft weggeschreven
function LeesDiag([string]$bestand) {
    $p = Join-Path $LocalData "Diagnose\$bestand"
    if (-not (Test-Path $p)) { return $null }
    $f = Get-Item $p
    if ($vers -and $f.LastWriteTime -lt $vers) { return @{ Verouderd = $true; Tijd = $f.LastWriteTime } }
    # Een leeg bestand is een geldige uitkomst en geen fout: claimreal_Waterberging komt sinds #664
    # in de BAU-varianten leeg terug omdat geen enkele regio nog een opgave heeft. Get-Content -Raw
    # geeft dan null, en daar liep dit stuk op stuk.
    $t = Get-Content $p -Raw
    if ($null -eq $t) { $t = '' }
    return @{ Verouderd = $false; Tekst = $t.Trim(); Tijd = $f.LastWriteTime }
}

function Ontleed([string]$tekst) {
    # Vorm: 'maat;waarde|sleutel;getal|sleutel;getal'
    $h = @{}
    foreach ($rij in ($tekst -split '\|')) {
        $d = $rij -split ';'
        if ($d.Count -ge 2 -and $d[1] -match '^-?[\d.]+$') { $h[$d[0]] = [double]$d[1] }
    }
    return $h
}

function TrapB([string]$variant, [string]$jaar) {
    $casus = "${Scenario}_$variant"
    $j = $jaar -replace '^Stand',''

    # Piekbui. De opgave hangt aan het basisjaar en is op bestaand bebouwd gebied gemaskeerd, dus
    # hij hoort in elke variant en elk zichtjaar hetzelfde te zijn. Dat maakt hem een harde
    # invariant: wijkt hij af, dan is er iets met de maskering of met de basisjaarstand.
    # Het bestand heet sinds #720 piekbuiberging_*; onder de oude naam waterberging_* stond dezelfde
    # uitdraai, en die naam droeg ook de sector, wat precies de verwarring was die #720 opruimt.
    $wb = LeesDiag "piekbuiberging_${casus}_$j.txt"
    if ($null -eq $wb)          { Meld 'B' $casus "$j piekbui" 'GEEN DATA' 'bestand ontbreekt' 'draai /Diagnose/GenerateAll' }
    elseif ($wb.Verouderd)      { Meld 'B' $casus "$j piekbui" 'GEEN DATA' "bestand van $($wb.Tijd.ToString('dd-MM HH:mm'))" 'na de runstart' }
    else {
        $v = Ontleed $wb.Tekst
        $okOpgave = [math]::Abs($v['opgave'] - 497.023) -lt 0.01
        Meld 'B' $casus "$j piekbuiopgave is de bekende invariant" $(if ($okOpgave) {'PASS'} else {'FAIL'}) ("{0:N3} mln m3" -f $v['opgave']) '497,023 mln m3'
        $okWb = ($v['aanbod_op_wbcellen'] -eq 0)
        Meld 'B' $casus "$j bergingscellen tellen niet mee in de dekking" $(if ($okWb) {'PASS'} else {'FAIL'}) ("{0}" -f $v['aanbod_op_wbcellen']) 'exact 0'

        # Twee posten die de dekkingsgraad bepalen en tot #720 nergens werden gerapporteerd. Geen
        # PASS of FAIL: er is geen norm voor. Ze staan hier omdat een dekkingsgraad die zonder deze
        # twee getallen wordt overgenomen een puntgetal suggereert dat het niet is.
        if ($v['aanbod_totaal'] -gt 0) {
            $klemAandeel   = $v['aanbod_zonder_opgave'] / $v['aanbod']
            $buitenAandeel = $v['aanbod_buiten_bbg'] / $v['aanbod_totaal']
            $dekking       = $v['gedekt'] / $v['opgave']
            $dekkingOngekl = [math]::Min($v['aanbod'], $v['opgave']) / $v['opgave']
            Meld 'B' $casus "$j dekkingsgraad piekbui, bandbreedte" 'INFO' ("{0:P1} geklemd op blok, {1:P1} ongeklemd" -f $dekking, $dekkingOngekl) 'lees als bandbreedte'
            Meld 'B' $casus "$j aanbod dat de dekking niet haalt" 'INFO' ("{0:P1} valt door de blokklemming, {1:P1} ligt buiten bebouwd gebied" -f $klemAandeel, $buitenAandeel) 'zie #720 en #741'
        }

        # De drie aanbodposten horen op te tellen: de gemaskeerde som plus wat de maskering weglaat is
        # het aanbod zoals het tot #741 werd geteld. Sluit dat niet, dan is er iets met de begrenzing
        # of met een null in BBGSamengesteld, en dan klopt de dekkingsgraad ook niet.
        if ($null -ne $v['aanbod'] -and $null -ne $v['aanbod_buiten_bbg']) {
            $gat = [math]::Abs(($v['aanbod'] + $v['aanbod_buiten_bbg']) - $v['aanbod_totaal'])
            Meld 'B' $casus "$j aanbod binnen plus buiten is het totaal" $(if ($gat -lt 0.001) {'PASS'} else {'FAIL'}) ("gat {0:N4} mln m3" -f $gat) 'kleiner dan 0,001'
        }
    }

    # Grondbalans. De drie bestemmingen zijn deelverzamelingen van het verlies, dus ze hoeven niet
    # exact op te tellen, maar een gat groter dan een half procent betekent dat er een categorie
    # zoek is en niet dat er een restje naar een vierde bestemming gaat.
    $gb = LeesDiag "${casus}_${j}_grondbalans_bestemmingen.txt"
    if ($null -eq $gb)     { Meld 'B' $casus "$j grondbalans" 'GEEN DATA' 'bestand ontbreekt' 'draai /Diagnose/GenerateAll' }
    elseif ($gb.Verouderd) { Meld 'B' $casus "$j grondbalans" 'GEEN DATA' "bestand van $($gb.Tijd.ToString('dd-MM HH:mm'))" 'na de runstart' }
    else {
        $g = Ontleed ($gb.Tekst -replace ';(?=[a-z_]+;)', '|')
        $som = $g['verstedelijking_vruchtbaar_ha'] + $g['nieuwenatuur_vruchtbaar_ha'] + $g['waterberging_vruchtbaar_ha'] - $g['overlap_verst_natuur_ha']
        $rest = $g['verdwenen_vruchtbaar_ha'] - $som
        $frac = if ($g['verdwenen_vruchtbaar_ha'] -gt 0) { $rest / $g['verdwenen_vruchtbaar_ha'] } else { 0 }
        Meld 'B' $casus "$j grondbalans sluit" $(if ([math]::Abs($frac) -lt 0.005) {'PASS'} else {'FAIL'}) ("rest {0:N1} ha, {1:P2}" -f $rest, $frac) 'onder 0,5 procent'
    }

    # Claimrealisatie. Kijk naar het uiterste over de regio's en niet naar het landelijke gemiddelde;
    # een landelijke 1,00 kan negen regio's onder de norm verbergen.
    foreach ($paar in @(@('claimreal_NL_woningen','wonen landelijk',0.99,1.01), @('claimreal_NL_banen','banen landelijk',0.99,1.06))) {
        $d = LeesDiag "${casus}_${j}_$($paar[0]).txt"
        if ($null -eq $d -or $d.Verouderd) { Meld 'B' $casus "$j $($paar[1])" 'GEEN DATA' 'ontbreekt of verouderd' 'draai /Diagnose/GenerateAll'; continue }
        $w = [double]($d.Tekst -replace ',','.')
        Meld 'B' $casus "$j claimrealisatie $($paar[1])" $(if ($w -ge $paar[2] -and $w -le $paar[3]) {'PASS'} else {'FAIL'}) ("{0:N4}" -f $w) ("{0} tot {1}" -f $paar[2], $paar[3])
    }

    # Wonen per NVM-regio. Beoordeel op het AANTAL regio's onder de norm en niet op het minimum:
    # het minimum zakt vanzelf naarmate de reeks vordert, want de claim groeit door terwijl de
    # ruimte opraakt, en een vaste ondergrens geeft daarom vanaf de latere zichtjaren altijd een
    # FAIL. Dat maakt de toets waardeloos. Het aantal regio's onder de norm is wel te vergelijken:
    # de oplevering van 28 augustus noteerde er negen op Y2120 voor de referentievarianten.
    $nvm = LeesDiag "${casus}_${j}_claimreal_NVM_woningen.txt"
    if ($null -ne $nvm -and -not $nvm.Verouderd) {
        $r = @($nvm.Tekst -split ';' | Where-Object { $_ -match '^\d' } | ForEach-Object { [double]$_ } | Where-Object { $_ -gt 0 })
        if ($r.Count -gt 0) {
            $min    = ($r | Measure-Object -Minimum).Minimum
            # LET OP: 0,99 is de ALARMDREMPEL van dit harnas en niet de norm van het model.
            # Het model hanteert 0,98 als ondergrens, als ModelParameters/Advanced/ClaimRealisatie_NormOnder,
            # en dat is de waarde achter de kolommen OnderNorm, OpNorm en BovenNorm die in de levering komen.
            # De twee tellen dus verschillend: op NbSGenuanceerd Y2060 geeft deze drempel 26 regio's en de
            # modelnorm 22. Dat verschil is bewust, een levering wordt strenger beoordeeld dan het model
            # zichzelf beoordeelt, maar het moet uit de regelnaam blijken. Wie ze gelijk wil trekken zet
            # $drempel op /ModelParameters/Advanced/ClaimRealisatie_NormOnder; dan verandert het oordeel.
            $drempel = 0.99
            $onder  = @($r | Where-Object { $_ -lt $drempel }).Count
            # Ruim boven de negen van 28 augustus, zodat gewone spreiding geen alarm geeft en een
            # verdubbeling wel. NbSGenuanceerd zat op Y2120 op 33 en dat is een echte bevinding.
            $grens  = 15
            Meld 'B' $casus "$j NVM-regio's onder alarmdrempel $drempel" $(if ($onder -le $grens) {'PASS'} else {'FAIL'}) ("$onder van $($r.Count), laagste {0:N4}" -f $min) "hoogstens $grens; let op: modelnorm is 0,98"
        }
    }

    # Waterbergingsclaim. Sinds #664 hoort BAU en BAU2 geen enkele regio met een opgave te hebben.
    $wbc = LeesDiag "${casus}_${j}_claimreal_Waterberging.txt"
    if ($null -ne $wbc -and -not $wbc.Verouderd) {
        $r = @($wbc.Tekst -split ';' | Where-Object { $_ -match '^\d' } | ForEach-Object { [double]$_ })
        if ($variant -like 'BAU*') {
            Meld 'B' $casus "$j waterberging heeft geen opgave" $(if ($r.Count -eq 0) {'PASS'} else {'FAIL'}) "$($r.Count) regio's met een opgave" '0, zie #664'
        } elseif ($r.Count -gt 0) {
            $min = ($r | Measure-Object -Minimum).Minimum
            Meld 'B' $casus "$j waterberging haalt de opgave" $(if ($min -ge 0.99) {'PASS'} else {'FAIL'}) ("{0:N4} over {1} regio's" -f $min, $r.Count) 'minstens 0,99'
        }
    }
}

# --------------------------------------------------------- trap C: wat zelf gerekend moet worden
function TrapC([string]$variant, [string]$jaar) {
    $casus = "${Scenario}_$variant"
    $j = $jaar -replace '^Stand',''
    $env:DiagCasus = $casus
    $env:DiagJaar  = "'$j'"
    $env:LocalDataProjDir = $LocalData
    $log = Join-Path $env:TEMP "toets_${casus}_$j.log"
    if (Test-Path $log) { Remove-Item -LiteralPath $log -Force }

    & $Exe "/L$log" $Cfg '/Diagnose/GenerateAll' 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $errs = @(Select-String -Path $log -Pattern '\[E\]' -ErrorAction SilentlyContinue)
    Meld 'C' $casus "$j diagnoseharnas gedraaid" $(if ($code -eq 0 -and $errs.Count -eq 0) {'PASS'} else {'FAIL'}) "exit $code, $($errs.Count) foutregels" 'exit 0, geen foutregels'
}

# ----------------------------------------------------------------------------------- uitvoeren
Write-Host ""
Write-Host "LocalData : $LocalData"
Write-Host "varianten : $($Varianten -join ', ')"
if ($vers) { Write-Host "vers vanaf: $($vers.ToString('yyyy-MM-dd HH:mm'))" } else { Write-Host "vers vanaf: niet gezet, verouderde uitdraaien worden NIET ontmaskerd" -ForegroundColor Yellow }
Write-Host ""
Write-Host ("{0,-5} {1,-22} {2,-40} {3,-10} {4}" -f 'trap','casus','toets','oordeel','gemeten')
Write-Host ("-" * 120)

foreach ($v in $Varianten) {
    TrapA $v
    $pad = Join-Path $LocalData "Allocatie\${Scenario}_$v"
    $standen = @(Get-ChildItem $pad -Directory -Filter 'Stand*' -ErrorAction SilentlyContinue |
                 Where-Object { $_.Name -notmatch 'vintage' } | ForEach-Object { $_.Name })
    if ($Zichtjaren.Count -gt 0) { $standen = @($standen | Where-Object { $Zichtjaren -contains ($_ -replace '^Stand','') }) }
    foreach ($s in $standen) {
        if ($TrapC) { TrapC $v $s }
        TrapB $v $s
    }
}

# ------------------------------------------------------------------------------------- rapport
$nFail = @($script:Regels | Where-Object { $_.Oordeel -eq 'FAIL' }).Count
$nGeen = @($script:Regels | Where-Object { $_.Oordeel -eq 'GEEN DATA' }).Count
$nPass = @($script:Regels | Where-Object { $_.Oordeel -eq 'PASS' }).Count

$md = @()
$md += "# Toets van de oplevering"
$md += ""
$md += "LocalData: $LocalData"
$md += "Gedraaid: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
$md += "Codestand: $(git -C (Split-Path (Split-Path $Cfg -Parent) -Parent) rev-parse --short HEAD 2>$null)"
$md += ""
$md += "PASS $nPass, FAIL $nFail, GEEN DATA $nGeen."
$md += ""
$md += "GEEN DATA is geen PASS. Het betekent dat de run de uitdraai niet heeft weggeschreven of dat"
$md += "het bestand ouder is dan de runstart, en dus dat die toets niet is uitgevoerd."
$md += ""
$md += "| trap | casus | toets | oordeel | gemeten | verwacht |"
$md += "|---|---|---|---|---|---|"
foreach ($r in $script:Regels) { $md += "| $($r.Trap) | $($r.Casus) | $($r.Toets) | $($r.Oordeel) | $($r.Gemeten) | $($r.Verwacht) |" }
$md -join "`r`n" | Set-Content $Rapport -Encoding UTF8

Write-Host ""
Write-Host "PASS $nPass, FAIL $nFail, GEEN DATA $nGeen" -ForegroundColor $(if ($nFail -gt 0) {'Red'} elseif ($nGeen -gt 0) {'Yellow'} else {'Green'})
Write-Host "rapport: $Rapport"
if ($nFail -gt 0) { exit 1 }
