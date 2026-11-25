<#
================================================================================================
 Waakhond.ps1: GeoDmsRun starten met een plek in de gedeelde rij, een waakhond op voortgang en een geheugenrem
================================================================================================

 Wordt ingelezen door RunAllocatie.ps1, RunIndicatoren.ps1 en ToetsOplevering.ps1 (. .\Waakhond.ps1) en levert de
 functie Invoke-GeoDmsRun. Een GeoDmsRun kan vastlopen zonder te eindigen: op 11 november 2026 draaiden in een
 allocatie van Noord-Holland (GeoDMS 20.28.0.m, Y2040, Provincie_Werken Iter_13) acht threads ruim twee uur
 op volle kracht, terwijl het log stil stond en het proces in een meting van tien seconden niets las, niets
 schreef en geen paginafout maakte. Een script dat op het einde wacht, ziet dat nooit.

 De waakhond telt daarom elke meting als teken van leven waarin het log groeit of het proces bytes leest of
 schrijft of een paginafout maakt. Processortijd telt niet: het vastgelopen proces gebruikte acht kernen.
 Blijft elk teken van leven WaakhondMinuten minuten uit, dan stopt hij het proces op zijn PID en geeft hij de
 reden terug, met de laatste voortgangsregel uit het log (item en iteratie) en de bezette threads, zodat er
 iets is voor een melding bij GeoDMS. Een proces dat rekent, leest of schrijft of raakt nieuw geheugen; een
 kwartier zonder een van die drie hoort daar niet bij. In twee landelijke runs van november 2026 was de
 langste stilte tussen twee logregels drie minuten.

 DE GEDEELDE RIJ
 Op OVSRV08 draaien zes tot acht sessies die elk GeoDMS-runs starten, op 128 GB fysiek geheugen en een
 commitlimiet van 616 GB. Op 12 november 2026 groeide een meting die niemand had aangemeld tot 210 GB; het
 fysieke geheugen zakte onder 10 GB en de rem van een andere sessie stopte haar provinciale proefrun. Daarom
 vraagt Invoke-GeoDmsRun eerst een plek in een gedeelde rij: een map met een json-bestand per claim, met wat
 er draait, de werkkopie, de soort (landelijk of regionaal), de verwachte piek van het eigen geheugen en de
 PID's. Hij start GeoDmsRun pas als de claim past:
   - de lopende claims, elk met zijn verwachte piek of zijn werkelijke eigen geheugen als dat hoger is, plus
     het werkelijke eigen geheugen van de GeoDMS-processen zonder claim (Hestia, een GUI, een meting uit de
     shell), plus de eigen verwachte piek blijven onder RijBudgetGB;
   - een landelijke claim start niet naast een andere landelijke run;
   - naast een landelijke run loopt hooguit een grote regionale; een regionale claim tot RijKleinGB telt daarbij
     niet mee en hoeft alleen in het budget te passen. De landelijke allocatie gebruikt meer eigen geheugen dan de
     machine fysiek heeft, dus een grote run ernaast vertraagt hem; een opvraging van een paar items nauwelijks.
 Wie eerder vroeg, gaat voor zodra hij past; een latere claim die nu past naast de lopende en de eerdere die
 ook passen, gaat ertussendoor. Na afloop verdwijnt de claim. Een claim waarvan het proces weg is (de GeoDmsRun
 als die al loopt, anders het script dat wacht) ruimt de rij zelf op, zodat er na een herstart of een gestopt
 proces niets blijft hangen; hij kijkt op PID en starttijd, want Windows geeft een vrijgekomen PID weer uit.
 De rij regelt geen voorrang tussen sessies; die spreekt de coordinatie af in C:\LocalData\Coordinatie\rij.md.
 Hij telt het eigen geheugen en niet het vrije fysieke geheugen. Het budget is afgestemd op OVSRV08; op een
 machine met minder geheugen gelden alleen de regels over landelijke en regionale runs echt. Get-RijStand toont
 wat er in de rij staat.

 DE GEHEUGENREM
 Een claim is een schatting, en een run die erboven groeit, houdt de rij niet tegen. Op 16 november 2026 groeide
 een meting met een claim van 180 GB tot 587,5 GB eigen geheugen; de machine kwam op 615,6 van 616 GB commit en
 de run gaf 41 keer "memory allocation failed". Daarom meet Invoke-GeoDmsRun, zolang de GeoDmsRun loopt, elke
 RijRemMeetSeconden seconden het eigen geheugen van dat proces, zoals de rij het meet, en de commit van de
 machine. Hij stopt de run op zijn PID:
   - als het eigen geheugen boven RijRemFactor keer de claim komt;
   - als de commit van de machine boven RijMaxCommitGB komt en deze run van de lopende runs in de rij het verst
     boven zijn claim zit (eigen geheugen min claim, in GB). Een run die binnen zijn claim blijft, stopt dus nooit
     zolang een andere erboven zit; blijven ze allemaal binnen hun claim, dan stopt de run die het dichtst tegen
     zijn claim aan zit. Is een andere run al door zijn rem gestopt maar nog niet weg, dan wacht de rem die af.
 Een GeoDMS-proces zonder claim (een GUI, Hestia, een meting uit de shell) kan de rem niet stoppen; het telt
 alleen mee in de commit. Eens per minuut meten, zoals de waakhond, is te traag: dezelfde dag groeide een andere
 meting in 3 minuten tot boven 150 GB. De reden komt als [E]-regel onder het log. RunAllocatie.ps1 en
 RunIndicatoren.ps1 starten een stap die de rem stopte niet opnieuw, want hij groeit dan weer tot dezelfde grens;
 geef hem een hogere claim.

 DE LOCALDATA
 Test-LocalData stopt een script voor zijn eerste GeoDmsRun als -LocalData een andere map is dan die waar GeoDMS
 schrijft; Get-GeoDmsLocalData leidt die map af zoals GeoDMS dat doet (ObjectVision/RSopen#911).
================================================================================================
#>

# Hoe vaak de waakhond kijkt, in seconden.
$WaakhondMeetSeconden = 60

# De gedeelde rij: de map met de claims; het budget voor de som van de pieken in GB, onder RijMaxCommitGB; de
# GeoDMS-processen die zonder claim meetellen met hun eigen geheugen; en hoe vaak een wachtende claim opnieuw kijkt, in
# seconden.
$RijStandaardMap = 'C:\LocalData\Coordinatie\rij'
$RijBudgetGB     = 480
$RijProcesNamen  = @('GeoDmsRun', 'GeoDmsGuiQt')
$RijMeetSeconden = 15
# Tot hoeveel GB verwachte piek een regionale claim klein is: hij mag naast een landelijke en een grote regionale run
# starten als hij in het budget past.
$RijKleinGB      = 40
# Hoe vaak een claim die blijft wachten dat opnieuw in het log zet, in minuten; een verandering in wie er voor gaat
# meldt hij meteen.
$RijMeldMinuten  = 15
# De geheugenrem (zie de kop): boven hoeveel keer zijn claim het eigen geheugen een run stopt; boven welke commit van de
# machine in GB hij de run stopt die het verst boven zijn claim zit, de grens die de coordinatie aanhoudt op een
# commitlimiet van 616 GB; en hoe vaak hij meet, in seconden.
$RijRemFactor       = 1.25
$RijMaxCommitGB     = 540
$RijRemMeetSeconden = 5

# Een eigen keten die dit bestand inleest zonder Write-Regel te kennen, krijgt dezelfde vorm als de scripts.
if (-not (Get-Command Write-Regel -CommandType Function -ErrorAction SilentlyContinue)) {
    function Write-Regel([string]$Tekst) { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Tekst" }
}

function Get-RijProcesStart([long]$ProcId) {
    # De starttijd van een proces in ticks (UTC), of 0 als het er niet is. Een PID alleen zegt niet genoeg: na een herstart
    # of een gestopt proces kan hetzelfde nummer bij een ander proces horen. Een getal en geen tekst, want ConvertFrom-Json
    # maakt in pwsh 7 van een tijdstip een datum, die daarna niet meer gelijk is aan de tekst.
    if ($ProcId -le 0) { return [long]0 }
    try { return (Get-Process -Id $ProcId -ErrorAction Stop).StartTime.ToUniversalTime().Ticks } catch { return [long]0 }
}

function Open-RijSlot([string]$Map) {
    # Een bestand dat maar een proces tegelijk open kan hebben. Wie de claims leest, beslist en zijn claim schrijft, houdt
    # het zolang vast, zodat twee wachtende runs niet tegelijk dezelfde vrije ruimte zien. Sterft de houder, dan sluit
    # Windows het bestand en is het slot weer vrij.
    $pad = Join-Path $Map 'rij.slot'
    $tot = (Get-Date).AddMinutes(2)
    while ($true) {
        try { return [IO.File]::Open($pad, 'OpenOrCreate', 'ReadWrite', 'None') }
        catch {
            if ((Get-Date) -gt $tot) { throw "Het slot van de rij ($pad) is al twee minuten bezet of niet te openen: $($_.Exception.Message)" }
            Start-Sleep -Milliseconds 200
        }
    }
}

function Write-RijClaim([string]$Bestand, $Claim) {
    # Alleen met het slot vast: wie de rij leest, leest dan nooit een half geschreven claim.
    [IO.File]::WriteAllText($Bestand, ($Claim | ConvertTo-Json))
}

function Get-RijToestand([string]$Map) {
    # Wat de rij nu ziet: de levende claims, oudste aanvraag eerst (de bestandsnaam begint met het tijdstip), elk met het
    # werkelijke eigen geheugen van zijn GeoDmsRun; de GeoDMS-processen zonder claim; en de dode claims, die hij
    # verwijdert. Een claim hoort bij zijn GeoDmsRun zodra die loopt, en daarvoor bij het script dat wacht. Een bestand dat
    # niet te lezen is, slaat hij over. Alleen aanroepen met het slot vast.
    $claims = @(); $dood = @(); $metClaim = @{}
    foreach ($f in @(Get-ChildItem -LiteralPath $Map -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name)) {
        try { $c = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json } catch { continue }
        $c | Add-Member -NotePropertyName Bestand -NotePropertyValue $f.FullName -Force
        $leeft = if ($c.geodmsStart) { (Get-RijProcesStart $c.geodmsPid) -eq [long]$c.geodmsStart }
                 else                { $c.pidStart -and ((Get-RijProcesStart $c.pid) -eq [long]$c.pidStart) }
        if (-not $leeft) {
            Remove-Item -LiteralPath $f.FullName -ErrorAction SilentlyContinue
            $dood += $c
            continue
        }
        $eigen = 0.0
        if ($c.geodmsStart) {
            $metClaim[[long]$c.geodmsPid] = $true
            try { $eigen = (Get-Process -Id $c.geodmsPid -ErrorAction Stop).PrivateMemorySize64 / 1GB } catch { }
        }
        $c | Add-Member -NotePropertyName EigenGB -NotePropertyValue $eigen -Force
        $claims += $c
    }
    $los = @(Get-Process -Name $RijProcesNamen -ErrorAction SilentlyContinue | Where-Object { -not $metClaim.ContainsKey([long]$_.Id) } |
        ForEach-Object { [pscustomobject]@{ Naam = $_.ProcessName; Pid = $_.Id; EigenGB = $_.PrivateMemorySize64 / 1GB } })
    return [pscustomobject]@{ Claims = $claims; ZonderClaim = $los; Dood = $dood }
}

function Test-RijPast {
    # Past Claim naast de claims in Voor (de lopende, en de eerdere wachtende die voor gaan) en de processen zonder claim
    # (samen ZonderClaimGB)? Geeft leeg terug als hij past, en anders de reden.
    param($Claim, [object[]]$Voor, [double]$ZonderClaimGB, [double]$BudgetGB)
    $voorGB = 0.0
    foreach ($v in $Voor) { $voorGB += [math]::Max([double]$v.piekGB, [double]$v.EigenGB) }
    $landelijk = @($Voor | Where-Object { $_.soort -eq 'landelijk' }).Count
    $regionaal = @($Voor | Where-Object { $_.soort -ne 'landelijk' -and [double]$_.piekGB -gt $RijKleinGB }).Count
    $klein     = $Claim.soort -ne 'landelijk' -and [double]$Claim.piekGB -le $RijKleinGB
    if ($Claim.soort -eq 'landelijk' -and $landelijk -gt 0) { return 'er gaat al een landelijke run voor' }
    if ($Claim.soort -eq 'landelijk' -and $regionaal -gt 1) { return "er gaan $regionaal grote regionale runs voor, en naast een landelijke past er hooguit een" }
    if ($Claim.soort -ne 'landelijk' -and -not $klein -and $landelijk -gt 0 -and $regionaal -gt 0) { return "er gaan al een landelijke en een grote regionale run voor (boven $RijKleinGB GB)" }
    $som = $voorGB + $ZonderClaimGB + [double]$Claim.piekGB
    if ($som -gt $BudgetGB) {
        return ("samen {0} GB, boven het budget van {1} GB ({2} GB van de claims voor deze, {3} GB zonder claim, {4} GB voor deze stap)" -f
            [math]::Round($som, 1), $BudgetGB, [math]::Round($voorGB, 1), [math]::Round($ZonderClaimGB, 1), [double]$Claim.piekGB)
    }
    return ''
}

function Format-RijClaim($c, [switch]$VoorDeze) {
    # Een claim in een regel voor het log: wat, in welke werkkopie, soort, piek of werkelijk geheugen, en welk proces. Met
    # VoorDeze zegt hij ook of een claim die voor gaat zelf nog wacht.
    $kopie  = if ($c.werkkopie) { Split-Path $c.werkkopie -Leaf } else { 'onbekende werkkopie' }
    $proces = if ($c.geodmsPid) { "GeoDmsRun $($c.geodmsPid)" } else { "script $($c.pid)" }
    $wacht  = if ($VoorDeze -and $c.status -eq 'wacht') { ', wacht ook en gaat voor' } else { '' }
    return ("{0} in {1} ({2}, {3} GB, {4}{5})" -f $c.wat, $kopie, $c.soort, [math]::Round([math]::Max([double]$c.piekGB, [double]$c.EigenGB), 1), $proces, $wacht)
}

function Wait-RijPlek {
    # Zet een claim in de rij en wacht tot hij past (zie de kop). Geeft een object terug met het claimbestand, de claim en
    # de seconden die hij wachtte. Breekt het wachten af, dan haalt hij de claim weg.
    param([double]$PiekGB, [string]$Soort, [string]$Wat, [string]$Werkkopie, [string]$Log, [string]$Map)

    if ($PiekGB -le 0 -or @('landelijk', 'regionaal') -notcontains $Soort) {
        throw "Invoke-GeoDmsRun: geef -RijPiekGB (de verwachte piek van het eigen geheugen in GB) en -RijSoort (landelijk of regionaal) mee; zie de kop van Waakhond.ps1"
    }
    if ($PiekGB -gt $RijBudgetGB) { throw "Invoke-GeoDmsRun: de verwachte piek van $PiekGB GB is groter dan het budget van de rij ($RijBudgetGB GB); deze stap past nooit" }
    if (-not (Test-Path -LiteralPath $Map)) { New-Item -ItemType Directory -Path $Map -Force | Out-Null }

    $claim = [ordered]@{
        wat         = $Wat
        werkkopie   = $Werkkopie
        soort       = $Soort
        piekGB      = $PiekGB
        status      = 'wacht'
        aangevraagd = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        gestart     = ''
        log         = $Log
        pid         = $PID
        pidStart    = (Get-RijProcesStart $PID)
        geodmsPid   = 0
        geodmsStart = [long]0
        remGestopt  = ''
    }
    $bestand = Join-Path $Map ('{0}_{1}.json' -f (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss_fff'), $PID)
    $begin = Get-Date
    $vorigeSleutel = $null
    $gemeld = $begin
    $geplaatst = $false
    try {
        while ($true) {
            $slot = Open-RijSlot $Map
            try {
                if (-not (Test-Path -LiteralPath $bestand)) { Write-RijClaim $bestand $claim }
                $t = Get-RijToestand $Map
                $losGB = [double](($t.ZonderClaim | Measure-Object EigenGB -Sum).Sum)
                # Wie loopt telt mee, en wie eerder vroeg en nu past ook, alsof hij al liep: die gaat voor. Een eerdere claim
                # die niet past, houdt deze niet op.
                $voor = @($t.Claims | Where-Object { $_.status -eq 'loopt' -and $_.Bestand -ne $bestand })
                foreach ($w in @($t.Claims | Where-Object { $_.status -eq 'wacht' })) {
                    if ($w.Bestand -eq $bestand) { break }
                    if (-not (Test-RijPast $w $voor $losGB $RijBudgetGB)) { $voor += $w }
                }
                $reden = Test-RijPast ([pscustomobject]$claim) $voor $losGB $RijBudgetGB
                if (-not $reden) {
                    $claim.status  = 'loopt'
                    $claim.gestart = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
                    Write-RijClaim $bestand $claim
                }
            } finally { $slot.Dispose() }

            foreach ($d in $t.Dood) { Write-Regel "rij       : dode claim opgeruimd: $(Format-RijClaim $d), aangevraagd $($d.aangevraagd)" }
            if (-not $reden) { break }
            # Melden als de reden of wie er voor gaat verandert, en anders elke RijMeldMinuten. De reden zonder getallen,
            # want het geheugen van de processen zonder claim verandert bij elke meting.
            $sleutel = ($reden -replace '[\d.,]+', '#') + '|' + (($voor | ForEach-Object { $_.Bestand }) -join ',')
            if ($sleutel -ne $vorigeSleutel -or ((Get-Date) - $gemeld).TotalMinutes -ge $RijMeldMinuten) {
                $wie = if ($voor.Count -gt 0) { ($voor | ForEach-Object { Format-RijClaim $_ -VoorDeze }) -join '; ' } else { 'niemand' }
                $los = if ($t.ZonderClaim.Count -gt 0) { ($t.ZonderClaim | ForEach-Object { "{0} {1} ({2} GB)" -f $_.Naam, $_.Pid, [math]::Round($_.EigenGB, 1) }) -join '; ' } else { 'geen' }
                Write-Regel ("wacht     : {0} wacht {1:N0} min op een plek in de rij: {2}. Voor gaan: {3}. Zonder claim: {4}." -f $Wat, ((Get-Date) - $begin).TotalMinutes, $reden, $wie, $los)
                $vorigeSleutel = $sleutel
                $gemeld = Get-Date
            }
            Start-Sleep -Seconds $RijMeetSeconden
        }
        $geplaatst = $true
    } finally {
        if (-not $geplaatst) { Remove-Item -LiteralPath $bestand -ErrorAction SilentlyContinue }
    }
    $wacht = ((Get-Date) - $begin).TotalSeconds
    if ($vorigeSleutel) { Write-Regel ("plek      : {0} na {1:N1} min in de rij" -f $Wat, ($wacht / 60)) }
    return [pscustomobject]@{ Bestand = $bestand; Claim = $claim; Map = $Map; Wacht = $wacht }
}

function Get-RijStand {
    # Wat er nu in de rij staat, voor wie wil kijken: de claims, oudste aanvraag eerst, en de GeoDMS-processen zonder claim.
    # Ruimt dode claims op, net als een wachtende run.
    param([string]$Map = $RijStandaardMap)
    if (-not (Test-Path -LiteralPath $Map)) { return }
    $slot = Open-RijSlot $Map
    try { $t = Get-RijToestand $Map } finally { $slot.Dispose() }
    foreach ($c in $t.Claims) {
        [pscustomobject]@{ Status = $(if ($c.remGestopt) { 'gestopt door de rem' } else { $c.status }); Soort = $c.soort; PiekGB = $c.piekGB; EigenGB = [math]::Round($c.EigenGB, 1)
                           Wat = $c.wat; Werkkopie = $c.werkkopie; Pid = $(if ($c.geodmsPid) { $c.geodmsPid } else { $c.pid }); Sinds = $c.aangevraagd }
    }
    foreach ($l in $t.ZonderClaim) {
        [pscustomobject]@{ Status = 'zonder claim'; Soort = ''; PiekGB = $null; EigenGB = [math]::Round($l.EigenGB, 1)
                           Wat = $l.Naam; Werkkopie = ''; Pid = $l.Pid; Sinds = '' }
    }
}

function Test-RijRem {
    # Een meting van de geheugenrem (zie de kop): geeft leeg terug als de run door mag, en anders de reden om hem te stoppen.
    # Plek is wat Wait-RijPlek teruggaf, Proces de lopende GeoDmsRun, en Staat onthoudt wanneer hij voor het laatst meldde
    # dat de commit te hoog is terwijl een andere run voor gaat.
    param($Plek, [Diagnostics.Process]$Proces, [hashtable]$Staat)

    $piekGB = [double]$Plek.Claim.piekGB
    try { $Proces.Refresh(); $eigenGB = $Proces.PrivateMemorySize64 / 1GB } catch { return '' }
    if ($eigenGB -gt $RijRemFactor * $piekGB) {
        return ("geheugenrem: {0:N1} GB eigen geheugen, meer dan {1} keer de claim van {2} GB; PID {3} gestopt. Heeft deze stap echt zoveel nodig, geef hem dan een hogere claim (-RijPiekGB)" -f
            $eigenGB, $RijRemFactor, $piekGB, $Proces.Id)
    }
    $os = Get-CimInstance Win32_OperatingSystem -Property TotalVirtualMemorySize, FreeVirtualMemory -ErrorAction SilentlyContinue
    if (-not $os) { return '' }
    $commitGB = ($os.TotalVirtualMemorySize - $os.FreeVirtualMemory) / 1MB
    if ($commitGB -le $RijMaxCommitGB) { return '' }

    # Boven de grens stopt alleen de run die het verst boven zijn claim zit, en een stop die al loopt gaat voor; wie dat is,
    # staat in de rij. Lukt het lezen niet, dan probeert hij het bij de volgende meting opnieuw.
    try {
        $slot = Open-RijSlot $Plek.Map
        try {
            $t = Get-RijToestand $Plek.Map
            $lopend = @($t.Claims | Where-Object { $_.geodmsStart })
            $bezig  = @($lopend | Where-Object { $_.remGestopt -and $_.Bestand -ne $Plek.Bestand })
            $verst  = $lopend | Sort-Object { [double]$_.EigenGB - [double]$_.piekGB } -Descending | Select-Object -First 1
            $deze   = $bezig.Count -eq 0 -and $verst -and $verst.Bestand -eq $Plek.Bestand
            if ($deze) {
                $Plek.Claim.remGestopt = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
                Write-RijClaim $Plek.Bestand $Plek.Claim
            }
        } finally { $slot.Dispose() }
    } catch { return '' }

    $beschrijf = { param($c) "{0} ({1:N1} GB eigen, claim {2} GB)" -f $c.wat, [double]$c.EigenGB, [double]$c.piekGB }
    if (-not $deze) {
        if (-not $Staat.Gemeld -or ((Get-Date) - $Staat.Gemeld).TotalMinutes -ge $RijMeldMinuten) {
            $waarom = if ($bezig.Count -gt 0) { "de rem stopt al $(& $beschrijf $bezig[0])" } elseif ($verst) { "$(& $beschrijf $verst) zit verder boven zijn claim" } else { 'de rij is niet te lezen' }
            Write-Regel ("rem       : de machine staat op {0:N1} GB commit, boven {1} GB, maar {2} loopt door: {3}" -f $commitGB, $RijMaxCommitGB, $Plek.Claim.wat, $waarom)
            $Staat.Gemeld = Get-Date
        }
        return ''
    }
    $anderen = @($lopend | Where-Object { $_.Bestand -ne $Plek.Bestand } | ForEach-Object { & $beschrijf $_ })
    $naast = if ($anderen.Count -gt 0) { "verder in de rij: $($anderen -join '; ')" } else { 'er loopt geen andere run in de rij' }
    $plaats = if ($eigenGB -gt $piekGB) { 'het verst boven zijn claim' } else { 'het dichtst tegen zijn claim aan, en geen run zit erboven' }
    return ("geheugenrem: de machine staat op {0:N1} GB commit, boven de grens van {1} GB, en deze run zit met {2:N1} GB eigen geheugen tegen een claim van {3} GB {4} ({5}); PID {6} gestopt" -f
        $commitGB, $RijMaxCommitGB, $eigenGB, $piekGB, $plaats, $naast, $Proces.Id)
}

function Invoke-GeoDmsRun {
    # Vraagt een plek in de gedeelde rij, start GeoDmsRun met de gegeven argumenten zodra hij past, en wacht tot hij klaar
    # is, vastloopt of door de geheugenrem gestopt wordt. Geeft een object terug met Code (de exitcode), Reden (leeg, of
    # waarom de waakhond of de rem het proces stopte; die staat dan ook als [E]-regel onder het log), Gestopt (leeg,
    # 'vastgelopen' of 'geheugen') en Wacht (de seconden in de rij, die de aanroeper van de rekentijd aftrekt).
    # WaakhondMinuten 0 zet de waakhond uit, niet de rem.
    # RijPiekGB (de verwachte piek van het eigen geheugen in GB) en RijSoort (landelijk of regionaal) zijn verplicht. RijWat
    # zegt in de rij wat er draait, standaard het laatste argument; RijMap is alleen voor een toets een andere map dan de
    # gedeelde.
    param([string]$Exe, [string[]]$Argumenten, [string]$Log, [int]$WaakhondMinuten,
          [double]$RijPiekGB, [string]$RijSoort, [string]$RijWat = '', [string]$RijMap = '')

    if (-not $RijMap) { $RijMap = $RijStandaardMap }
    if (-not $RijWat) { $RijWat = [string]($Argumenten | Select-Object -Last 1) }
    # De werkkopie is de map boven cfg van de configuratie in de argumenten.
    $dms = [string]($Argumenten | Where-Object { $_ -like '*.dms' } | Select-Object -First 1)
    $werkkopie = if ($dms) { Split-Path (Split-Path $dms -Parent) -Parent } else { '' }
    $plek = Wait-RijPlek -PiekGB $RijPiekGB -Soort $RijSoort -Wat $RijWat -Werkkopie $werkkopie -Log $Log -Map $RijMap

    $reden = ''
    $gestopt = ''
    try {
        $psi = [Diagnostics.ProcessStartInfo]::new($Exe)
        $psi.Arguments = ($Argumenten | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' '
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow  = $true
        # De uitvoer op het scherm gooien de scripts weg, zoals voorheen met Out-Null. Lezen moet wel, anders loopt de pijp vol
        # en wacht GeoDmsRun op een lezer.
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $p = [Diagnostics.Process]::Start($psi)
        $p.BeginOutputReadLine()
        $p.BeginErrorReadLine()

        # Vanaf nu hoort de claim bij de GeoDmsRun: de rij leest zijn werkelijke geheugen, telt hem niet ook nog als proces
        # zonder claim, en ruimt de claim op zodra hij weg is.
        $plek.Claim.geodmsPid   = $p.Id
        $plek.Claim.geodmsStart = (Get-RijProcesStart $p.Id)
        $slot = Open-RijSlot $plek.Map
        try { Write-RijClaim $plek.Bestand $plek.Claim } finally { $slot.Dispose() }

        $vorige = ''
        $laatsteLeven = Get-Date
        $vorigeCpu = 0
        $vorigeThreads = @{}
        $remStaat = @{ Gemeld = $null }
        # De rem meet elke RijRemMeetSeconden, de waakhond elke WaakhondMeetSeconden.
        $waakhondKlok = [Diagnostics.Stopwatch]::StartNew()
        while (-not $p.WaitForExit($RijRemMeetSeconden * 1000)) {
            $rem = Test-RijRem -Plek $plek -Proces $p -Staat $remStaat
            if ($rem) {
                $reden = $rem
                $gestopt = 'geheugen'
                try { $p.Kill() } catch { }
                break
            }
            if ($waakhondKlok.Elapsed.TotalSeconds -lt $WaakhondMeetSeconden) { continue }
            $periode = $waakhondKlok.Elapsed.TotalSeconds
            $waakhondKlok.Restart()
            # Processortijd van het proces en per thread sinds de vorige meting, alleen voor de melding als hij vastloopt.
            $p.Refresh()
            $cpuKernen = ($p.TotalProcessorTime.TotalSeconds - $vorigeCpu) / $periode
            $vorigeCpu = $p.TotalProcessorTime.TotalSeconds
            $threadsBezig = 0
            $nuThreads = @{}
            foreach ($th in $p.Threads) {
                try { $s = $th.TotalProcessorTime.TotalSeconds } catch { continue }
                $nuThreads[$th.Id] = $s
                # Bezig: meer dan de helft van de meetperiode op een kern.
                if ($vorigeThreads.ContainsKey($th.Id) -and ($s - $vorigeThreads[$th.Id]) -gt $periode / 2) { $threadsBezig++ }
            }
            $vorigeThreads = $nuThreads
            if ($WaakhondMinuten -le 0) { continue }
            $c = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction SilentlyContinue
            if (-not $c) { continue }
            # De lengte via een open met gedeelde toegang: de mapvermelding van een bestand dat openstaat om te schrijven loopt achter.
            $logBytes = 0
            try { $fs = [IO.File]::Open($Log, 'Open', 'Read', 'ReadWrite'); $logBytes = $fs.Length; $fs.Close() } catch { }
            $nu = "$logBytes,$($c.ReadTransferCount),$($c.WriteTransferCount),$($c.PageFaults)"
            if ($nu -ne $vorige) { $laatsteLeven = Get-Date }
            $vorige = $nu
            $stil = ((Get-Date) - $laatsteLeven).TotalMinutes
            if ($stil -ge $WaakhondMinuten) {
                # Waar de engine bleef: de laatste voortgangsregel, met item en iteratie, uit het laatste stuk van het log.
                $laatste = ''
                try {
                    $fs = [IO.File]::Open($Log, 'Open', 'Read', 'ReadWrite')
                    $fs.Seek([math]::Max(0, $fs.Length - 256KB), 'Begin') | Out-Null
                    $staart = (New-Object IO.StreamReader($fs)).ReadToEnd()
                    $fs.Close()
                    $laatste = [string]($staart -split "`r?`n" | Where-Object { $_ -match '\[!\]' } | Select-Object -Last 1)
                } catch { }
                $reden = ("vastgelopen: {0:N0} minuten zonder loggroei, I/O of paginafouten; {1} van {2} threads bezig en {3:N1} kernen in gebruik in de laatste minuut; laatste voortgang: {4}; PID {5} gestopt door de waakhond" -f $stil, $threadsBezig, $nuThreads.Count, $cpuKernen, $laatste.Trim(), $p.Id)
                $gestopt = 'vastgelopen'
                $p.Kill()
                break
            }
        }
        $p.WaitForExit()
    } finally {
        # De plek vrijgeven, ook als het script hier wordt afgebroken. Lukt dat niet, dan ruimt de rij de claim op zodra de
        # GeoDmsRun weg is.
        Remove-Item -LiteralPath $plek.Bestand -ErrorAction SilentlyContinue
    }
    # Een gestopt proces krijgt zijn reden als [E]-regel onder zijn log, zodat wie het log later opent ziet waarom hij stopte. Een
    # proces dat midden in een regel stopt, laat het log zonder regeleinde achter; de [E]-regel komt dan op een eigen regel.
    if ($reden -and $Log) {
        $regeleinde = ''
        try {
            $fs = [IO.File]::Open($Log, 'Open', 'Read', 'ReadWrite')
            if ($fs.Length -gt 0) { $fs.Seek(-1, 'End') | Out-Null; if ($fs.ReadByte() -ne 10) { $regeleinde = "`r`n" } }
            $fs.Close()
        } catch { }
        ($regeleinde + "[E] Waakhond.ps1: $reden") | Add-Content -LiteralPath $Log -Encoding UTF8
    }
    # Wie een script aanroept en daarna $LASTEXITCODE leest, krijgt de exitcode van de laatste GeoDmsRun, zoals bij een
    # gewone aanroep met &.
    $global:LASTEXITCODE = $p.ExitCode
    return [pscustomobject]@{ Code = $p.ExitCode; Reden = $reden; Gestopt = $gestopt; Wacht = $plek.Wacht }
}

function Get-GeoDmsLocalData([string]$Cfg) {
    # De map die GeoDMS voor %LocalDataProjDir% neemt bij deze configuratie, op dezelfde manier afgeleid als GeoDMS dat doet
    # (GetLocalDataProjDir en GetConvertedGeoDmsRegKey in de broncode): de omgevingsvariabele GEODMS_directories_localDataProjDir
    # als die er is, anders LocalDataDir plus de naam van de map boven cfg. LocalDataDir komt uit GEODMS_directories_LocalDataDir
    # of uit het register, eerst de sleutel met de machinenaam en dan die van DMS. Een kale omgevingsvariabele LocalDataProjDir
    # leest GeoDMS niet. Zo gemeten met GeoDMS 20.28.0.m op 24 november 2026.
    if ($env:GEODMS_directories_localDataProjDir) { return $env:GEODMS_directories_localDataProjDir }
    $wortel = $env:GEODMS_directories_LocalDataDir
    $sleutels = @("HKCU:\Software\ObjectVision\$env:COMPUTERNAME\GeoDMS", 'HKCU:\Software\ObjectVision\DMS')
    foreach ($s in $sleutels) {
        if ($wortel) { break }
        $wortel = (Get-ItemProperty -LiteralPath $s -Name LocalDataDir -ErrorAction SilentlyContinue).LocalDataDir
    }
    if (-not $wortel) { throw "LocalDataDir staat niet in het register ($($sleutels -join ' of ')) en GEODMS_directories_LocalDataDir is leeg" }
    return Join-Path $wortel (Get-Item -LiteralPath $Cfg -ErrorAction Stop).Directory.Parent.Name
}

function Test-LocalData([string]$Cfg, [string]$LocalData) {
    # Stopt als -LocalData een andere map is dan die waar GeoDMS deze configuratie naar schrijft. De scripts toetsen invoer,
    # standen en uitdraaien in -LocalData, terwijl GeoDMS in zijn eigen map leest en schrijft en daar een andere reeks kan
    # overschrijven (ObjectVision/RSopen#911). Hoort voor de eerste GeoDmsRun van een script.
    $geodms = Get-GeoDmsLocalData $Cfg
    $vol = { param($p) [IO.Path]::GetFullPath($ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)).TrimEnd('\') }
    if (-not [string]::Equals((& $vol $LocalData), (& $vol $geodms), [StringComparison]::OrdinalIgnoreCase)) {
        Write-Regel "GESTOPT: -LocalData is $LocalData, maar GeoDMS leest en schrijft deze configuratie in $geodms."
        Write-Regel "GeoDMS leidt die map af uit LocalDataDir in het register plus de naam van de map boven cfg, en het script verlegt hem niet."
        Write-Regel "Laat -LocalData weg, of reken vanuit een werkkopie waarvan de map heet zoals de LocalData die je wilt."
        throw "-LocalData wijkt af van de map van GeoDMS ($geodms)"
    }
    Write-Regel "controle  : GeoDMS schrijft ook naar $geodms"
}
