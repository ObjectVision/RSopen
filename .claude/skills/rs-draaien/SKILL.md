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

Dezelfde val met een ander gezicht, gemeten op 2026-09-01: een ontkoppeld bestand dat niet op het domein past geeft `[E] FileTileArray Error: stored array ... holds N bytes, but the domain it is read into requires exactly M bytes`, en ook dat loopt af met exitcode 0. De gevraagde parameter komt dan leeg terug. Let op dat zo'n bestand op zichzelf wel gewoon leest: het attribuut rechtstreeks opvragen gaf exit 0 zonder een enkele foutregel. De fout ontstaat pas als het in een domein wordt gelezen dat de configuratie zelf afleidt, dus de melding zegt niet dat het bestand stuk is maar dat de twee kanten het over de omvang oneens zijn.

## Welke GeoDMS

Draai op de geinstalleerde build onder `C:\Program Files\ObjectVision`, op dit moment `GeoDms20.17.0.m`. Niet op de build uit Visual Studio in `C:\dev\GeoDms_2026\bin\Release\x64`. Die wordt opnieuw gecompileerd zonder dat de configuratie verandert, dus een run kan halverwege op een andere engine draaien dan waarmee hij begon, en een verschil in uitkomst valt dan niet meer toe te wijzen aan de configuratie. Op 2026-08-29 meldde Object Vision bovendien dat die build op dat moment niet stabiel was.

De versie staat op vier plekken: `geodmsversion` in `batch/RunAll.cmd`, de default van `-Version` in `run-item.ps1`, en `-Exe` in `Run2120.ps1` en `RunIndicatoren.ps1`. Controleer ze alle vier voordat je een lange run start, want een run die halverwege van engine wisselt is niet meer te toetsen.

## Wis het log voor elke stap

`GeoDmsRun` schrijft met `/L<pad>` naar een bestaand logbestand zonder het eerst leeg te maken. Een script dat na afloop op `[E]` grept vindt dan ook de fouten van de vorige run met datzelfde logpad, en meldt een geslaagde stap als mislukt. Dat kost zoekwerk, en erger: het maakt een echte fout onzichtbaar tussen de oude.

Wis het log dus aan het begin van elke stap:

```powershell
if (Test-Path $l) { Remove-Item -LiteralPath $l -Force }
& $Exe "/L$l" '/S1' '/S2' '/S3' $Cfg $Item 2>&1 | Out-Null
```

Toets daarnaast altijd op `[E]` en niet alleen op de exitcode; zie de memory over een GDAL-fout die exit 0 gaf.

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

### De zeef kost geen allocatie

Wil je weten wat een zeeftoets per zichtjaar wegzeeft, dan hoef je niet te alloceren. `Templates/VariantData_T.dms` bouwt `container Zeef` als een `for_each` over de zichtjaren, gevoed uit `StateBasisjaar`, de dichtheid, de plancapaciteit en de restricties. De zeef van Y2120 leest de allocatie van Y2110 dus niet, en alle zichtjaren zijn in een aanroep op te vragen.

Gemeten op 2026-09-01: alle negen zichtjaren van BAU, twee subsectoren, tien tellingen per zichtjaar, samen 2,5 minuten. Vraag ze in een aanroep op, want zonder CalcCache kost een tweede aanroep de hele basisdata opnieuw.

Bouw zo'n uitdraai als een `Diagnose<nummer>.dms` met een `AsList` over `/Classifications/Time/Zichtjaar/name`, zodat de reeks meebeweegt met `Model_FirstZichtjaar` en `Model_FinalYear` in plaats van dat de zichtjaren in het harnas worden herhaald.

Neem een zelftoets op zodra je een samengestelde toets met de hand nabouwt, bijvoorbeeld een OR waar je een term uit wilt laten. Zet de nabouw plus de weggelaten term naast het echte item en schrijf het verschil als kolom weg; staat die kolom niet overal op nul, dan meet je iets anders dan je denkt. Bij #586 hield dat de nabouw van `IsRestrictief` eerlijk toen een andere sessie halverwege de avond een term in diezelfde OR verving.

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

## Niet elke variant alloceert: BAU2 leent de stand van BAU

Sinds a9ca6b47 draait de allocatie van BAU2 niet meer. Hij leent de standtifs van BAU, en alleen zijn indicatoren draaien nog. Dat scheelt 7,71 uur per reeks, gemeten op de productierun van 1 september 2026.

De schakelaar is de kolom `StandVanVariant` in `cfg/main/VariantParameters/VariantK.dms`. Staat daar de eigen naam, dan alloceert de variant gewoon; staat er een andere naam, dan leest de indicatorenkant de tifs van die variant. Dat gebeurt op precies een plek, `Templates/Indicatoren_T/StandCasus_name`, die `@CASUS@` in `AllocatieFileName` vult. `Variant_rel` blijft die van de lenende variant, dus alle variantparameters worden gewoon van BAU2 gelezen en de zes koolstofkolommen blijven verschillen.

Wat dat voor het draaien betekent:

- `batch/Run2120.ps1` kent dit. Geef gewoon `-Varianten BAU,BAU2,NbSGenuanceerd` mee; BAU2 wordt overgeslagen met een regel in het log en zijn diagnose ook, want die meet de allocatie. Wel moet de uitlener in dezelfde aanroep meedraaien, anders stopt het script.
- `batch/RunAll.cmd`, `RunZichtjaren.cmd` en `RunScenarios.cmd` kennen dit NIET. Draai je BAU2 daarmee, dan alloceert hij alsnog en kost dat 7,71 uur voor een stand die byte-identiek wordt aan die van BAU. Gebruik voor een productiereeks `Run2120.ps1`.
- `batch/RunIndicatoren.ps1` hoeft niets te weten: de indicatorenkant lost het lenen zelf op.
- `batch/ToetsOplevering.ps1` meldt een lenende variant als INFO en niet als FAIL op een ontbrekende allocatiemap.

Er is geen map `Allocatie/WLO_hoog_BAU2` meer, en dat is geen fout. Beoordeel die stand bij BAU.

De aanname eronder is dat BAU en BAU2 op alles wat de allocatie raakt gelijk zijn, gemeten in #730. `Test-LeenAanname` in `Run2120.ps1` bewaakt dat omgekeerd: hij eist dat de kolommen waarop de twee VERSCHILLEN precies de bekende zes zijn, en dat de sector Landbouw niet wordt gealloceerd. Die tweede voorwaarde staat in `ModelParameters/SectorAllocRegio` en niet in VariantK, dus geen kolomvergelijking ziet hem.

Valt die toets om, zet `StandVanVariant` dan terug op de eigen naam en laat BAU2 weer alloceren. Aanzetten van de sector Landbouw doet hem ook omvallen, en terecht.

Let op bij een verkorte allocatie: lenen is alleen veilig als lener en uitlener op dezelfde `ModelParameters/Skeleton`-instellingen draaien. Verschillen die, dan leent BAU2 een stand die onder andere aannames is gemaakt en waarschuwt niets.

## Tag de codestand bij een productierun

Een productierun beslaat uren en loopt vaak op meerdere machines tegelijk, terwijl de branch ondertussen doorloopt. Zonder tag is achteraf niet meer vast te stellen welke code een uitdraai heeft gemaakt. Zet daarom bij de start een annotated tag op de commit die draait, met de conventie `oplevering_<project>_<datum>`:

```bash
git tag -a oplevering_NL2120_20260829 <commit> -m "..."
git push origin oplevering_NL2120_20260829
```

Zet in de boodschap wat later niet meer te reconstrueren is: welke varianten op welke machines, de zichtjaren, de engine, en de afwijkingen van de standaardopzet. Let op een detail dat anders twijfel zaait: de getagde commit hoeft niet de laatste te zijn die `cfg/` raakte. Een commit die alleen `.claude/` of `batch/` wijzigt verandert de berekening niet, maar schrijf dat expliciet in de tag, anders moet de lezer dat zelf uitzoeken.

Wat je niet in de tag zet is wat je niet hebt gecontroleerd. Draaien er meerdere machines, dan is `git rev-parse HEAD` op elke machine het bewijs; zonder dat bewijs hoort er een voorbehoud in de boodschap.

## Voor je begint

Draai `git status` en kijk naar de mtime van de bestanden die je gaat wijzigen, vlak voordat je schrijft. In deze werkkopie draaien regelmatig meerdere sessies tegelijk, geen aparte worktrees. Commit alleen je eigen bestanden met een expliciete `git add`.

In een worktree resolvet `%LocalDataProjDir%` naar `C:/LocalData/<naam van de map boven cfg>`, waar de ontkoppelde data van het hoofdproject niet staat. End-to-end-tests op dataniveau kunnen daar dus niet. Leg geen junction naar `C:/LocalData/RSopen_NL2120` zonder dat expliciet af te stemmen: dat geeft schrijfrisico in de echte ontkoppelde data.

## Toetsen terwijl een ander draait: een losse kopie van cfg

Op deze werkkopie draaien vaak meerdere sessies. Schrijven in `cfg/` botst dan met elke lopende reeks GeoDmsRun-stappen, want elke stap parseert de configuratie opnieuw. Wachten op een schrijfvenster hoeft niet: de configuratie is 4,5 MB en alle databronnen hangen aan `%sourceDataDir%`, dus een kopie doet het net zo goed.

```bash
cp -r cfg Data git.txt /pad/naar/scratchpad/RSopen_NL2120/
```

`Data` en `git.txt` moeten mee omdat niet alle bronnen aan `%sourceDataDir%` hangen. Vier hangen aan `%ProjDir%/Data`: de SOMERS-datasheet, de CBS-kerncijfers per wijk en buurt, en twee classificatietabellen. Samen 3,4 MB. Zonder die map parseert de kopie schoon met exit 0 en valt hij pas om zodra een keten de csv opent, met 49 foutregels op `cannot open dataset`. Dat is hetzelfde patroon als bij een verkeerde mapnaam hieronder, alleen bouwt een andere variabele het pad op.

De mapnaam boven `cfg` moet gelijk zijn aan die van het project. `%LocalDataProjDir%` resolvet naar `C:/LocalData/<naam van de map boven cfg>`, en onder een andere naam vindt de configuratie de ontkoppelde bestanden niet. Dat valt niet op bij het parsen maar pas als een keten er een leest: op 2026-08-31 viel de grootwatervlag om op `BBG2022_25m_Modus_Nederland.tif` in een map die niet bestond.

Met de goede naam leest de kopie dezelfde ontkoppelde bestanden als de werkkopie. Dat is veilig zolang je alleen items zonder storage opvraagt. Wil je een uitdraai zien, zet de `StorageName` van dat ene item dan om naar de scratchpad, zodat er niets in de gedeelde `LocalData/Diagnose` belandt terwijl een ander daar schrijft.

"Geen storage" is echter niet af te lezen aan het item dat je opvraagt. Een schrijfstap kan achter een meta-keuze zitten, en dan draagt het item zelf geen `StorageName` terwijl de gekozen tak er wel een heeft. Twee gevallen die op 2026-09-01 zijn gemeten:

- `Landgebruikskaart/Result_SA` kiest op `ModelParameters/LandUseMapOntkoppeld`. Die staat op FALSE, dus de keuze valt op `Write_Result_SA` en de kaart wordt weggeschreven in de gedeelde LocalData. Zet hem in je kopie op TRUE, dan leest `Read_Result_SA` de bestaande tif.
- `SourceData/Grondgebruik/IBIS/Result/RestrictiefWonen` schrijft via de Make-tak een tif zodra een wijziging de fingerprint verandert. Vraag een niveau dieper, dus `Calc_RestrictiefWonen`, dan blijft het lezen.

De regel die daaruit volgt: zoek voor je een item opvraagt niet alleen naar `StorageName` op dat item, maar volg ook elke `:= =` meta-keuze in de keten erboven naar de tak die werkelijk wordt gekozen. Bewijs achteraf dat er niets is geschreven door de mtimes onder `%LocalDataProjDir%` voor en na te vergelijken; dat is sterker dan de redenering dat er niets geschreven zou worden.

Zelfs dat is niet genoeg, en het strandde op 2026-09-02 alsnog. Een item zonder storage kan een supplier hebben die er wel een draagt, willekeurig ver de keten in. Een diagnose op `CO2FlowTovBasisjaar` voor Y2120 liep via `PrevIndicatoren` door negen zichtjaren terug en raakte onderweg `Landgebruikskaart/Write_Result_SA`, waarmee tien landgebruikskaarten in de opleveringsmap opnieuw werden weggeschreven. Dezelfde aanroep op Y2040 deed dat niet, want daar wijst `PrevZichtjaar` naar het basisjaar en is de keten kort. De ketenlengte hangt dus af van het zichtjaar, en een meting die op het ene jaar veilig is, is dat op het andere niet.

**How to apply:** vertrouw niet op "ik vraag een item zonder storage op". Laat de kopie naar een eigen `%LocalDataProjDir%` wijzen door de map boven `cfg` een eigen naam te geven, en neem de kosten van het opnieuw maken van de ontkoppelde bestanden voor lief. Kan dat niet, houd het dan bij een enkel zichtjaar met een korte keten, en vergelijk hoe dan ook de mtimes voor en na.

De winst is dat de kopie ook een plek is om schakelaars om te zetten die in de werkkopie van iemand anders zijn. Een meting met `IndicatorRegio_ref` op een andere indeling kan zo zonder aan de gedeelde `ModelParameters/Advanced.dms` te komen.

Wat het oplevert: op 2026-08-31 vond een sessie er drie fouten mee die anders in het schrijfvenster hadden gezeten, waaronder een `AsList` die de padnamen samenvoegde in plaats van de waarden. Die had exit 0 gegeven en een tabel met tien regels padnaam.

## De processenlijst zegt niet of de baan vrij is

Een reeks diagnosestappen draait elk item als een eigen GeoDmsRun-proces. Tussen twee items zit een gat van een paar seconden waarin er niets draait. Wie op dat moment kijkt ziet een lege lijst en concludeert dat de machine vrij is.

Kijk dus naar de mtime van het logbestand van de ander, of vraag het gewoon. Op 2026-08-31 scheelde die vraag het onderbreken van een reeks die op vijftien van de twintig items stond.
