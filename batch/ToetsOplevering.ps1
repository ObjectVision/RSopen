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
    [string]   $Exe        = 'C:\Program Files\ObjectVision\GeoDms20.23.1.m\GeoDmsRun.exe',
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

# Verwachte setgroottes per variant, uit de OP-tabel na #721 en het stedelijke vrijstaande pakket van #847.
$OPSetGrootte = @{ 'BAU'=28; 'BAU2'=28; 'NbSGenuanceerder'=40; 'NbSGenuanceerd'=40 }

# De normen voor de controlewaarden van de tabellen Checks en ChecksBasisjaar staan sinds #833 in cfg/main/Diagnose.dms,
# in de kolommen norm_onder en norm_boven, met de afweging bij de rij. Het harnas schrijft per casus en zichtjaar een csv
# <casus>_<jaar>_checks.csv met naam, waarde, ondergrens, bovengrens en oordeel; dit script leest alleen dat oordeel.
# Een nieuwe norm hoort dus in die tabel en niet hier.

function Get-Zichtjaren([string]$casusPad) {
    Get-ChildItem $casusPad -Directory -Filter 'Stand Y*' -ErrorAction SilentlyContinue |
        ForEach-Object { $_.Name } | Sort-Object
}

# ---------------------------------------------------------------- trap A: wat er op schijf staat
function Get-Uitlener([string]$variant) {
    # Leest VariantK/StandVanVariant, zodat het harnas weet welke variant haar stand leent.
    # Faalt de parse, dan geeft hij de variant zelf terug: liever een overbodige toets dan een
    # gemiste. Het pad naar de configuratie is afgeleid van $LocalData en kan afwijken; daarom
    # zoekt hij ook naast het script.
    if ($script:LeenTabel -eq $null) {
        $script:LeenTabel = @{}
        $kandidaten = @(
            (Join-Path (Split-Path $PSScriptRoot -Parent) 'cfg\main\VariantParameters\VariantK.dms')
        )
        foreach ($vk in $kandidaten) {
            if (-not (Test-Path $vk)) { continue }
            $t = Get-Content $vk -Raw
            $mn = [regex]::Match($t, "attribute<[^>]+>\s+name\s*:\s*\[(.*?)\]", 'Singleline')
            $ms = [regex]::Match($t, "attribute<[^>]+>\s+StandVanVariant\s*:\s*\[(.*?)\]", 'Singleline')
            if (-not ($mn.Success -and $ms.Success)) { continue }
            $n = @([regex]::Matches($mn.Groups[1].Value, "'([^']*)'") | ForEach-Object { $_.Groups[1].Value })
            $u = @([regex]::Matches($ms.Groups[1].Value, "'([^']*)'") | ForEach-Object { $_.Groups[1].Value })
            for ($i = 0; $i -lt $n.Count -and $i -lt $u.Count; $i++) { $script:LeenTabel[$n[$i]] = $u[$i] }
            break
        }
    }
    if ($script:LeenTabel.ContainsKey($variant)) { return $script:LeenTabel[$variant] }
    return $variant
}

function TrapA([string]$variant) {
    $casus = "${Scenario}_$variant"
    $pad   = Join-Path $LocalData "Allocatie\$casus"

    # Een variant die haar stand van een andere leent heeft geen eigen allocatiemap, en dat is
    # geen fout. VariantK/StandVanVariant zegt van wie ze leent; staat daar een andere naam, dan
    # is de allocatie bewust niet gedraaid en beoordeel je die stand bij de uitlener. Zie
    # Templates/Indicatoren_T/StandCasus_name en de leentoets in batch/Run2120.ps1.
    $uitlener = Get-Uitlener $variant
    if ($uitlener -and $uitlener -ne $variant) {
        Meld 'A' $casus 'allocatie geleend' 'INFO' "leest de stand van ${Scenario}_$uitlener" 'beoordeel die stand bij de uitlener'
        return
    }

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
            $nSub = ((($inhoud -split 'subsector_set=')[1] -split ';')[0] -split ',').Count
            # Het SS-nummer in de bestandsnaam is het aantal subsectoren waarmee de stand is geschreven; de
            # legenda hoort daar precies zoveel namen voor te dragen.
            $nSS  = if ($params[0].Name -match 'SS-(\d+)') { [int]$Matches[1] } else { -1 }
            $okOP = ($OPSetGrootte.ContainsKey($variant) -and $nOP -eq $OPSetGrootte[$variant])
            Meld 'A' $casus "$jaar legenda, aantal pakketten" $(if ($okOP) {'PASS'} else {'FAIL'}) "$nOP" "$($OPSetGrootte[$variant])"
            Meld 'A' $casus "$jaar legenda, aantal subsectoren" $(if ($nSub -eq $nSS) {'PASS'} else {'FAIL'}) "$nSub" "SS-$nSS in de bestandsnaam"
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

function NietVanToepassing($d) {
    # Diagnose/Voorwaarde zet een controle waarvan de sector of het indicatordomein in deze run niet meedoet
    # op null, en een uitdraai buiten de tabel op een regel die met niet_van_toepassing begint.
    return ($null -ne $d -and -not $d.Verouderd -and ($d.Tekst -eq 'null' -or $d.Tekst -like 'niet_van_toepassing*'))
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

function ToetsChecks([string]$casus, [string]$jaarlabel) {
    # Een regel per rij met een norm. NVT is een rij waarvan de sector of het indicatordomein in deze run niet meedoet
    # (Diagnose/Voorwaarde), GEEN_GETAL een rij met een norm die geen getal opleverde, GEEN_NORM een waarde om te lezen.
    $bestand = "${casus}_${jaarlabel}_checks.csv"
    $p = Join-Path $LocalData "Diagnose\$bestand"
    if (-not (Test-Path $p)) { Meld 'B' $casus "$jaarlabel controletabel" 'GEEN DATA' 'bestand ontbreekt' "draai de diagnose, $bestand"; return }
    $f = Get-Item $p
    if ($vers -and $f.LastWriteTime -lt $vers) { Meld 'B' $casus "$jaarlabel controletabel" 'GEEN DATA' "bestand van $($f.LastWriteTime.ToString('dd-MM HH:mm'))" 'na de runstart'; return }
    foreach ($r in (Import-Csv $p)) {
        $onder = if ($r.ondergrens -ne '') { $r.ondergrens } else { '-' }
        $boven = if ($r.bovengrens -ne '') { $r.bovengrens } else { '-' }
        $verwacht = "$onder tot $boven"
        switch ($r.oordeel) {
            'PASS'       { Meld 'B' $casus "$jaarlabel $($r.naam)" 'PASS' $r.waarde $verwacht }
            'FAIL'       { Meld 'B' $casus "$jaarlabel $($r.naam)" 'FAIL' $r.waarde $verwacht }
            'GEEN_GETAL' { Meld 'B' $casus "$jaarlabel $($r.naam)" 'GEEN DATA' "geen getal: $($r.waarde)" $verwacht }
            'NVT'        { if ($r.ondergrens -ne '' -or $r.bovengrens -ne '') { Meld 'B' $casus "$jaarlabel $($r.naam)" 'INFO' 'niet van toepassing' 'zie Voorwaarde in Diagnose.dms' } }
            default      { }
        }
    }
}

function TrapBasisjaar([string]$variant) {
    ToetsChecks "${Scenario}_$variant" 'Basisjaar'
}

function TrapB([string]$variant, [string]$jaar) {
    $casus = "${Scenario}_$variant"
    $j = $jaar -replace '^Stand',''

    # Piekbui. De opgave, het aanbod op bergingscellen en de sluiting van het aanbod hebben een norm en staan sinds #833 als
    # rijen piekbui_* in Checks. Hier blijft alleen de dekkingsgraad als INFO, want daar is geen norm voor.
    # Het bestand heet sinds #720 piekbuiberging_*; onder de oude naam waterberging_* stond dezelfde
    # uitdraai, en die naam droeg ook de sector, wat precies de verwarring was die #720 opruimt.
    $wb = LeesDiag "piekbuiberging_${casus}_$j.txt"
    if ($null -eq $wb)          { Meld 'B' $casus "$j piekbui" 'GEEN DATA' 'bestand ontbreekt' 'draai /Diagnose/GenerateAll' }
    elseif ($wb.Verouderd)      { Meld 'B' $casus "$j piekbui" 'GEEN DATA' "bestand van $($wb.Tijd.ToString('dd-MM HH:mm'))" 'na de runstart' }
    elseif (NietVanToepassing $wb) { Meld 'B' $casus "$j piekbui" 'INFO' 'niet van toepassing' (($wb.Tekst -split ';')[1]) }
    else {
        $v = Ontleed $wb.Tekst
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
    }

    # De grondbalans en de claimrealisatie, landelijk en per NVM-regio, zijn sinds #833 rijen in Checks
    # (grondbalans_rest_fractie, claimreal_NL_woningen, claimreal_NL_banen, claimreal_NVM_onder_alarm).

    # Waterbergingsclaim. Sinds #664 hoort BAU en BAU2 geen enkele regio met een opgave te hebben. Blijft hier en niet
    # in Checks, want de norm hangt van de variant af en een rij in die tabel kent een band voor alle varianten.
    $wbc = LeesDiag "${casus}_${j}_claimreal_Waterberging.txt"
    if (NietVanToepassing $wbc) { Meld 'B' $casus "$j waterberging" 'INFO' 'niet van toepassing' 'de sector Waterberging doet in deze run niet mee' }
    elseif ($null -ne $wbc -and -not $wbc.Verouderd) {
        $r = @($wbc.Tekst -split ';' | Where-Object { $_ -match '^\d' } | ForEach-Object { [double]$_ })
        if ($variant -like 'BAU*') {
            Meld 'B' $casus "$j waterberging heeft geen opgave" $(if ($r.Count -eq 0) {'PASS'} else {'FAIL'}) "$($r.Count) regio's met een opgave" '0, zie #664'
        } elseif ($r.Count -gt 0) {
            $min = ($r | Measure-Object -Minimum).Minimum
            Meld 'B' $casus "$j waterberging haalt de opgave" $(if ($min -ge 0.99) {'PASS'} else {'FAIL'}) ("{0:N4} over {1} regio's" -f $min, $r.Count) 'minstens 0,99'
        }
    }

    ToetsChecks $casus $j
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

function TrapCBasisjaar([string]$variant) {
    $casus = "${Scenario}_$variant"
    $env:DiagCasus = $casus
    $env:LocalDataProjDir = $LocalData
    $log = Join-Path $env:TEMP "toets_${casus}_basisjaar.log"
    if (Test-Path $log) { Remove-Item -LiteralPath $log -Force }

    & $Exe "/L$log" $Cfg '/Diagnose/GenerateBasisjaar' 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $errs = @(Select-String -Path $log -Pattern '\[E\]' -ErrorAction SilentlyContinue)
    Meld 'C' $casus 'basisjaarcontroles gedraaid' $(if ($code -eq 0 -and $errs.Count -eq 0) {'PASS'} else {'FAIL'}) "exit $code, $($errs.Count) foutregels" 'exit 0, geen foutregels'
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
    if ($TrapC) { TrapCBasisjaar $v }
    TrapBasisjaar $v
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
