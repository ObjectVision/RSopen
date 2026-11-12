<#
================================================================================================
 Waakhond.ps1: GeoDmsRun starten met een waakhond op voortgang
================================================================================================

 Wordt ingelezen door RunAllocatie.ps1 en RunIndicatoren.ps1 (. .\Waakhond.ps1) en levert de functie
 Invoke-GeoDmsRun. Een GeoDmsRun kan vastlopen zonder te eindigen: op 11 november 2026 draaiden in een
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
================================================================================================
#>

# Hoe vaak de waakhond kijkt, in seconden.
$WaakhondMeetSeconden = 60

function Invoke-GeoDmsRun {
    # Start GeoDmsRun met de gegeven argumenten en wacht tot hij klaar is of vastloopt. Geeft een object terug met Code
    # (de exitcode) en Reden (leeg, of waarom de waakhond het proces stopte). WaakhondMinuten 0 zet de waakhond uit.
    param([string]$Exe, [string[]]$Argumenten, [string]$Log, [int]$WaakhondMinuten)

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

    $reden = ''
    $vorige = ''
    $laatsteLeven = Get-Date
    $vorigeCpu = 0
    $vorigeThreads = @{}
    while (-not $p.WaitForExit($WaakhondMeetSeconden * 1000)) {
        # Processortijd van het proces en per thread sinds de vorige meting, alleen voor de melding als hij vastloopt.
        $p.Refresh()
        $cpuKernen = ($p.TotalProcessorTime.TotalSeconds - $vorigeCpu) / $WaakhondMeetSeconden
        $vorigeCpu = $p.TotalProcessorTime.TotalSeconds
        $threadsBezig = 0
        $nuThreads = @{}
        foreach ($th in $p.Threads) {
            try { $s = $th.TotalProcessorTime.TotalSeconds } catch { continue }
            $nuThreads[$th.Id] = $s
            # Bezig: meer dan de helft van de meetperiode op een kern.
            if ($vorigeThreads.ContainsKey($th.Id) -and ($s - $vorigeThreads[$th.Id]) -gt $WaakhondMeetSeconden / 2) { $threadsBezig++ }
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
            $p.Kill()
            break
        }
    }
    $p.WaitForExit()
    # Wie een script aanroept en daarna $LASTEXITCODE leest, krijgt de exitcode van de laatste GeoDmsRun, zoals bij een
    # gewone aanroep met &.
    $global:LASTEXITCODE = $p.ExitCode
    return [pscustomobject]@{ Code = $p.ExitCode; Reden = $reden }
}
