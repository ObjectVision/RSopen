---
name: rs-draaien
description: Het RSopen-model draaien en een wijziging in cfg/ toetsen met GeoDmsRun, van een goedkope check per item tot een volledige allocatierun. Gebruik dit voordat je een configwijziging als werkend meldt, bij vragen over rekentijden, en wanneer een run gericht ingekort moet worden.
---

# RSopen draaien en toetsen

Vier trappen, van goedkoop naar duur. Klim niet hoger dan de vraag vereist. Een wijziging melden als werkend zonder minstens trap 1 is niet toegestaan.

## Trap 1: laadt het (seconden)

```powershell
& "C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe" "/L$env:TEMP\rs.log" "C:\ProjDir\RSopen_NL2120\cfg\main.dms" "/pad/naar/item"
```

Of via het meegeleverde script, dat de projectversie kiest, de tijd meet en de foutregels filtert:

```powershell
.\.claude\skills\rs-draaien\scripts\run-item.ps1 -Item "/Indicatoren/WLO_hoog_BAU/Zichtjaren/Y2030/Stand/Aantal_Woningen_Totaal"
```

Draai dit uit PowerShell, niet uit de Bash-tool. Die zet `/L` en `/pad/naar/item` om naar Windows-paden en dan faalt de aanroep.

Exitcodes: 0 is goed, 1 is een rekenfout of een gefaalde IntegrityCheck, 2 is een parse- of laadfout. Foutregels staan in het log met `[E]`.

Maar exit 0 is niet genoeg om een stap goed te keuren. Een ontbrekend bronbestand kan met exit 0 aflopen terwijl de fout alleen in het log staat. Gemeten op 2026-08-27 met een claim-CSV die niet bestond: `[E] GDAL Error: cannot open dataset ... No such file or directory`, exitcode 0, en de gevraagde statistiek kwam leeg terug. Toets in een batch dus altijd het log op `[E]` naast de exitcode, anders draait een lange run door op invoer die er niet is.

## Welke GeoDMS

Draai op de geinstalleerde build onder `C:\Program Files\ObjectVision`, op dit moment `GeoDms20.17.0.m`. Niet op de build uit Visual Studio in `C:\dev\GeoDms_2026\bin\Release\x64`. Die wordt opnieuw gecompileerd zonder dat de configuratie verandert, dus een run kan halverwege op een andere engine draaien dan waarmee hij begon, en een verschil in uitkomst valt dan niet meer toe te wijzen aan de configuratie. Op 2026-08-29 meldde Object Vision bovendien dat die build op dat moment niet stabiel was.

De versie staat op vier plekken: `geodmsversion` in `batch/RunAll.cmd`, de default van `-Version` in `run-item.ps1`, en `-Exe` in `Run2120.ps1` en `RunIndicatoren.ps1`. Controleer ze alle vier voordat je een lange run start, want een run die halverwege van engine wisselt is niet meer te toetsen.

## Nooit op procesnaam opruimen

Op OVSRV08 draaien regelmatig meerdere sessies tegelijk, en een productierun kan uren beslaan. Ruim GeoDmsRun daarom nooit op naam op:

```powershell
Get-Process -Name GeoDmsRun | Stop-Process -Force   # FOUT
```

Dat raakt elk GeoDmsRun-proces op de machine, ongeacht welke werkkopie eronder draait. Op 2026-08-27 om 17:30 kostte dat de productierun van #658 een zichtjaar en een herstart. Gebruik het PID, of filter op het configuratiepad zodat de productiekopie buiten schot blijft:

```powershell
Get-CimInstance Win32_Process -Filter "Name='GeoDmsRun.exe'" |
  Where-Object { $_.CommandLine -notmatch 'RSopen_NL2120_productie' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Zelfde reden om een lus met GeoDmsRun-aanroepen niet tegen een tijdslimiet aan te laten lopen: wordt zo'n aanroep afgekapt, dan ruimt de harness de procesboom op. Draai lange lussen in de achtergrond of met een ruime timeout.

De grens van deze trap: exit 0 op een groot attribuut zonder IntegrityCheck bewijst alleen parse, naamresolutie en domeincheck, dus UpdateMetaInfo. Een keten over negen miljoen cellen die in 0,002 s klaar is, is niet gematerialiseerd. Kijk altijd naar de rekentijd voordat je conclusies trekt. TIFFOpen-fouten op ontkoppelde bestanden vuren wel al bij UpdateMetaInfo, want die lezen de header.

## Trap 2: klopt het (seconden tot minuten)

Een assertie is een `IntegrityCheck` op het onderliggende item, met de exitcode als testuitslag:

```
attribute<float32> Som (Domein) := add(...), IntegrityCheck = "all(abs(this - 1f) < 0.001f)";
```

`IntegrityCheck = "this"` op een parameter die zelf de check is geeft "Invalid Recursion in UpdateMetaInfo". Zet de check dus op de data, niet op de conclusie.

IntegrityChecks van suppliers vuren ook als je een afhankelijk item opvraagt, dus een check dieper in de keten werkt als kanarie.

Werkelijke waarden zien gaat via een tekstbestand:

```
parameter<String> Waarde := string(sum(...))
, StorageName = "='%LocalDataProjDir%/Diagnose/mijn_check.txt'"
, StorageType = "str";
```

Een waarde eenmalig aflezen kan ook zonder tekstbestand, met de actie `@statistics` als los argument voor het itempad:

```powershell
& $Exe "/L$log" $Cfg '@statistics' '/Classifications/Time/Zichtjaar/YearRange_rel'
```

Let op de vorm. `@statistics` is een eigen argument. Plak je het achter het itempad, dan zoekt GeoDMS een item dat zo heet en krijg je "not found" met exit 1, wat leest als een configuratiefout terwijl het een aanroepfout is. `Run2120.ps1` haalt op deze manier de zichtjaren uit de configuratie in plaats van ze in het script te herhalen.

Verder rekent GeoDmsRun alleen door wat naar een storage gaat. Vraag je een item op met een `StorageName`, dan schrijft hij dat bestand ook echt weg; op 2026-08-28 belandden zo twee verificatie-items als losse tifs in een opleveringsmap. Wil je alleen toetsen, kies dan een item zonder storage, of een IntegrityCheck.

Semantiek van een operator of een randgeval bewijs je het snelst in een losse minimale .dms in de scratchpad, met eigen unitdeclaraties. Neem daar altijd een bewust falende kanarie in op, zodat je weet dat exit 1 ook echt werkt.

## Trap 3: de ketentriggers (minuten)

`CommitChecks` in `cfg/main.dms` dwingt hele deelketens af via ExplicitSuppliers: `MaakBaseData1`, `MaakBaseData2`, `MaakVariantData1`, `MaakVariantData2`, `MaakAllocatieFirstZichtjaar`, plus de drie claimrealisatie-checks. Bedoeld om voor een commit te zien of het model nog loopt, niet voor productie.

`Diagnose.dms` levert de inhoudelijke controlewaarden. Aansturing via de omgevingsvariabelen `DiagCasus` en `DiagJaar`. Zie de skill rs-toetsen voor wat je met die waarden doet.

Die twee werken niet hetzelfde. `DiagCasus` voedt een gewone parameter, dus `WLO_hoog_BAU` volstaat. `DiagJaar` voedt een meta-expressie, dus de waarde moet zelf aanhalingstekens dragen: `'Y2040'` en niet `Y2040`. Zonder die aanhalingstekens wordt het zichtjaar als itemnaam gelezen en krijg je `Unknown identifier 'Y2040'`, een melding die naar het diagnose-item wijst en niet naar de omgevingsvariabele. De default in de configuratie doet het goed, want die staat er met `quote(...)` omheen.

Meetharnassen per issue staan als `Diagnose<nummer>.dms` naast `Diagnose.dms`, met een `#include` in `cfg/main.dms`. Ze zijn tijdelijk en horen weg zodra de getallen in het issue staan.

## Trap 4: allocatie draaien

Voor het testen van het allocatiemechanisme hoeft de hele sectorlijst niet mee. Beperk `ModelParameters/SectorAllocRegio` in `cfg/main/ModelParameters.dms` tot de regels die je nodig hebt: commentarieer de rest in `Elements/Text` uit en zet `unit<UInt8> SectorAllocRegio := range(uint8, 0b, <aantal>b)` op het overgebleven aantal. Let op de komma's: de eerste actieve regel heeft geen voorloopkomma, de rest wel. Terugzetten niet vergeten.

De uitkomst voor de overgebleven sector is identiek aan die in de volledige run, mits die sector niet van verdringing door de weggelaten sectoren afhangt.

Gemeten rekentijden, zichtjaar 2030, WLO_hoog_NbSGenuanceerd, op deze machine:

| Wat | Tijd |
|---|---|
| volledige lijst, 7 regels, sinds de cumulatieve vormtoets van #643 | 72 min |
| alleen Waterberging op Waterbergingsregio | 6,3 min |
| alleen Wonen op NVM | 8 min |
| alleen Werken op NVM, 30 iteraties | 18 min |
| Wonen op NVM plus Waterberging | 12,6 min |
| Diagnose-set met 30 indicatorwaarden, los van de allocatie | 7,3 min |

Een volledig zichtjaar koud herbouwd kost ongeveer 64 minuten: basisdata circa 100 s, variantdata circa 230 s, allocatie circa 3.850 s, indicatoren circa 1.030 s, diagnose circa 460 s.

Twee valkuilen bij het inkorten. `Classifications/Modellering/StandVar_Prep` hangt af van `SectorAllocRegio/Uq_Sectors/HasWerkenSector`, dus zonder werken verdwijnen de banen-standvariabelen en breekt alles wat daarop leunt. En de bestandsnaam van de standtifs bevat `SS-<aantal xSubsectors>`, maar `Sector/xSubsector` telt alle gedefinieerde sectoren en niet alleen de actieve, dus die naam blijft `SS-11` en bestaande tifs blijven vindbaar.

Voor indicatorcontroles is de allocatie vaak helemaal niet nodig: met `StandAllocatieOntkoppeld` op TRUE, de default, leest de indicatorenkant de stand uit de tifs.

## Voor je begint

Draai `git status` en kijk naar de mtime van de bestanden die je gaat wijzigen, vlak voordat je schrijft. In deze werkkopie draaien regelmatig meerdere sessies tegelijk, geen aparte worktrees. Commit alleen je eigen bestanden met een expliciete `git add`.

In een worktree resolvet `%LocalDataProjDir%` naar `C:/LocalData/<naam van de map boven cfg>`, waar de ontkoppelde data van het hoofdproject niet staat. End-to-end-tests op dataniveau kunnen daar dus niet. Leg geen junction naar `C:/LocalData/RSopen_NL2120` zonder dat expliciet af te stemmen: dat geeft schrijfrisico in de echte ontkoppelde data.
