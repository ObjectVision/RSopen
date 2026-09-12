---
name: rs-draaien
description: Het RSopen-model draaien en een wijziging in cfg/ toetsen met GeoDmsRun, van een goedkope check per item tot een volledige allocatierun. Gebruik dit voordat je een configwijziging als werkend meldt, bij vragen over rekentijden, en wanneer een run gericht ingekort moet worden.
---

# RSopen draaien en toetsen

Vier trappen, van goedkoop naar duur. Klim niet hoger dan de vraag vereist. Een wijziging melden als werkend zonder minstens trap 1 is niet toegestaan.

## Wat een stap kost, en wanneer een allocatie echt nodig is

Een zware run is alles wat alloceert of basedata of variantdata genereert; een enkel item opvragen of een indicator narekenen op een bestaande stand valt daarbuiten. Verantwoord een zware run vooraf: wat wil je meten, kan dat op een bestaande stand, en zo nee waarom niet. Bijna elke vraag over beschikbaarheid, zeef, claims of brondata is in seconden tot minuten te beantwoorden. Een allocatie is alleen nodig voor de vraag wat er op een plek terechtkomt, dus voor verdringing en realisatie.

Gemeten op 2026-09-01 op GeoDms20.17.0.m:

| Soort stap | Kosten |
|---|---|
| geos-buffer met poly2grid over AdminDomain (3.912 polygonen) | 3 s per item, piek 0,6 GB |
| parse-check op een enkel item zonder storage | 3 s |
| zeefmeting over negen zichtjaren, inclusief variantdata voor twee varianten | 3,4 min |
| schade-uitdraai op een ontkoppelde stand | 300 s |
| `/Diagnose/GenerateAll` | 400 tot 960 s |
| allocatie van een zichtjaar | 45 tot 70 min |

De prijs van een vergridding zit in het aantal geometrieen en niet in de omvang van het domein: poly2grid raakt alleen de cellen onder de polygonen. Een geos-bewerking inschatten als een zware rasterbewerking zit er twee ordes naast.

Gaat er toch een zware run aan, kijk dan eerst wie er kan meeliften. De meeste vragen zijn indicator- of zeefvragen op een stand die de run toch al maakt, en die kosten niets extra zolang ze in dezelfde aanroep worden meegevraagd (zie Meerdere items in een aanroep). De passagier moet zijn item vooraf aanleveren, want achteraf aanhaken kan niet. Wat een volgende reeks moet meenemen hoef je niet bij te houden: dat is `git log <laatste opleveringstag>..HEAD`.

## Trap 1: laadt het (seconden)

```powershell
& "C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe" "/L$env:TEMP\rs.log" "<werkkopie>\cfg\main.dms" "/pad/naar/item"
```

Of via het meegeleverde script, dat de projectversie kiest, de tijd meet en de foutregels filtert:

```powershell
.\.claude\skills\rs-draaien\scripts\run-item.ps1 -Item "/Indicatoren/WLO_hoog_BAU/Zichtjaren/Y2040/Stand/Aantal_Woningen_Totaal"
```

Draai dit uit PowerShell, niet uit de Bash-tool. Die zet `/L` en `/pad/naar/item` om naar Windows-paden en dan faalt de aanroep.

Exitcodes: 0 is goed, 1 is een rekenfout of een gefaalde IntegrityCheck, 2 is een parse- of laadfout. Foutregels staan in het log met `[E]`.

Exit 0 is niet genoeg om een stap goed te keuren. Twee gemeten gevallen lopen met exit 0 af terwijl de fout alleen in het log staat en de gevraagde waarde leeg terugkomt: een ontbrekend bronbestand (`[E] GDAL Error: cannot open dataset ... No such file or directory`, 2026-08-27, een claim-CSV) en een ontkoppeld bestand dat niet op het domein past (`[E] FileTileArray Error: stored array ... holds N bytes, but the domain it is read into requires exactly M bytes`, 2026-09-01). Dat tweede bestand leest op zichzelf gewoon: het attribuut rechtstreeks opvragen gaf exit 0 zonder foutregel. De fout ontstaat pas in het domein dat de configuratie afleidt, dus de melding zegt dat de twee kanten het over de omvang oneens zijn en niet dat het bestand stuk is. Toets in een batch dus altijd het log op `[E]` naast de exitcode, anders draait een lange run door op invoer die er niet is.

De grens van deze trap: exit 0 op een groot attribuut zonder IntegrityCheck bewijst alleen parse, naamresolutie en domeincheck, dus UpdateMetaInfo. Een keten over negen miljoen cellen die in 0,002 s klaar is, is niet gematerialiseerd. Kijk altijd naar de rekentijd voordat je conclusies trekt. TIFFOpen-fouten op ontkoppelde bestanden vuren wel al bij UpdateMetaInfo, want die lezen de header.

Een leverancierslijst is tekst en geen graaf. Een naam in `generates/Alles_lijst` van `Templates/Indicatoren_T/Export.dms` die niet als parameter in `generates` bestaat, of een `ExplicitSuppliers`-pad dat niet oplost, valt bij het laden niet op en merk je pas als de export draait, aan het eind van een run. Grep daarom na elke merge waarin `Export.dms` meekomt elke naam uit `Alles_lijst` tegen de parameters in `generates`. Tot #779 stond die lijst als een regel van duizenden tekens en verloor een mergeconflict er stil zes leveranciers uit; sindsdien staat hij regel voor regel, maar de controle blijft nodig.

### Bij een meta-expressie moet je elke tak instantieren

Een meta-expressie, `:= =` gevolgd door een keuze tussen expressiestrings, kiest zijn tak bij het instantieren. Er komt maar een tak in de boom te hangen en de andere wordt niet eens geparseerd. Toets je een willekeurige instantiatie, dan zegt exit 0 alleen iets over de tak die daar gekozen werd.

Op 2026-09-04 blokkeerde dat de productierun drie pogingen lang: `IsRestrictief_OokBinnenPlancapaciteit` in de zichtjaar-zeef verwees naar een item dat door #759 was verwijderd, maar alleen in de tak voor werken met de kantoorverdikking aan. Drie subsectoren namen de `const(FALSE)`-tak en gaven exit 0 met nul foutregels; alleen Zak_dienstverlening viel om.

Zoek voor je toetst dus eerst op welke schakelaars en namen de expressie vertakt, en draai een instantiatie per tak:

```powershell
foreach ($sub in 'Zak_dienstverlening','Nijverheid','Logistiek','Detailhandel') {
  $Item = '/VariantData/BAU/Zeef/Y2040/SectorxSubsectoren/Werken/'+$sub+'/IsBeschikbaar'
  ...
}
```

Dezelfde redenering geldt voor de sectorpoorten in de templates, zoals `Sector_name == lowercase('Werken')`, en voor schakelaars uit `ModelParameters` en `VariantK`. Een tak die in de geteste variant uitstaat is ongetoetste code. En exit 0 op zo'n resolve-check bewijst nog steeds alleen UpdateMetaInfo: zes seconden per subsector is te snel om gerekend te hebben, de bevestiging komt uit een `@statistics` op het onderliggende item.

Een meta-expressie kan bovendien niet genest worden in een gewone expressie; de `=`-keuze staat altijd op het niveau van het item zelf.

### Meerdere items in een aanroep

`GeoDmsRun` neemt elk argument dat niet met `@` of `/` begint als itempad en werkt ze na elkaar af in hetzelfde proces. Elk item krijgt een eigen paar regels `{ Updating::[[item]]` en `} Updating::[[item]] (n secs)` in het log, dus de rekentijd per item blijft leesbaar. Faalt een item, dan loopt de lus door met het volgende, en het proces eindigt met exit 1 en een `[E]`-regel voor het gefaalde item (gemeten 2026-09-04 met een opzettelijk ontbrekend derde item: 2,4 s, exit 1, twee Updating-paren, een foutregel).

Dit is de manier om werk te delen dat verschillende casussen gemeen hebben, zoals de indicatorenexport van meerdere varianten voor hetzelfde zichtjaar: alles onder `SourceData`, `BaseData` en `Classifications` wordt dan een keer ingelezen. `batch/RunIndicatoren.ps1` doet dat achter `-Gebundeld`. Twee kanttekeningen: er is een exitcode voor alle items samen, dus de status per item moet uit het log komen, en of de engine gedeelde tussenresultaten tussen twee items in het geheugen houdt is niet gemeten.

Kies dit boven een verzamelitem met `ExplicitSuppliers` in de configuratie wanneer de items naar gedeelde paden schrijven of wanneer niet alle casussen uit de lijst mee moeten: het verzamelitem trekt alles gelijktijdig en over de hele lijst, de commandoregel precies wat je opgeeft en na elkaar.

### De export per bestand of per domein

`RunIndicatoren.ps1` vraagt `Zichtjaren/Export/Generate_Indicatoren` en dat is de hele set, ruim tachtig bestanden per casus en zeventig minuten per variant. Wil je minder, dan hoef je daar niet omheen te bouwen: `Zichtjaren/Export/generates` heeft een parameter per uitvoerbestand en `generates/Themas` een parameter per domein (Grondgebruik, Wonen, Werken, Water, Natuur, Landbouw, Koolstof, Sloop, Tabellen).

```powershell
$g = '/Indicatoren/WLO_hoog_BAU/Zichtjaren/Export/generates/'
$items = @(($g+'NieuweNatuur'), ($g+'BT_Exogeen'), ($g+'Themas/Koolstof'))
& $Exe "/L$log" '/S1' '/S2' '/S3' $Cfg @items
```

Zet daar dezelfde omgevingsvariabelen omheen als het batchscript: `ExportZichtjaar`, `IndicatorRegio`, `StandAllocatieOntkoppeld`, `VariantDataOntkoppeld`, en haal `LocalDataProjDir` weg. Gemeten op 2026-09-09: vier natuuritems en het thema Koolstof voor twee varianten samen 16,6 minuten, tegen zeventig minuten per variant voor de volle export.

### Zet haakjes om elk element van de itemlijst

In PowerShell bindt de komma sterker dan de plus. `@($g+'a', $g+'b')` wordt daardoor niet een lijst van twee paden maar een enkele string, want de komma maakt eerst `@('a', $g)` en de plus plakt dat aan `$g` vast. GeoDmsRun krijgt dan alle paden als een argument, zoekt een item met spaties in de naam, en eindigt met exit 2 op een melding die naar de configuratie wijst in plaats van naar de aanroep. Schrijf dus `@(($g+'a'), ($g+'b'))`.

## Welke GeoDMS

Draai op de geinstalleerde build onder `C:\Program Files\ObjectVision`, op dit moment `GeoDms20.17.0.m`. Niet op een build uit Visual Studio: die wordt opnieuw gecompileerd zonder dat de configuratie verandert, dus een run kan halverwege op een andere engine draaien dan waarmee hij begon, en een verschil in uitkomst valt dan niet meer toe te wijzen aan de configuratie.

De versie staat op vier plekken: `geodmsversion` in `batch/RunAll.cmd`, de default van `-Version` in `run-item.ps1`, en `-Exe` in `Run2120.ps1` en `RunIndicatoren.ps1`. Controleer ze alle vier voordat je een lange run start.

## Geheugen: de registerknoppen staan per machine

Een allocatie werkt structureel door de pagefile: een zichtjaar van de BAU-reeks van augustus 2026 piekte op een CommitCharge van 217 GB op een machine met 128 GB. Twee allocaties tegelijk op een machine is daarom geen optie; keten ze achter elkaar. Een diagnosestap van een paar minuten kan er wel naast.

GeoDMS leest zijn geheugenbudget uit `HKCU\Software\ObjectVision\<machinenaam>\GeoDMS`, dus per machine apart. Loop op een nieuwe machine eerst deze drie waarden na:

- `ResourceAwareScheduling` op 0. Op 2 (enforce) parkeert de scheduler threads tot twaalf keer toe zonder dat de piek daalt; de broncode zet hem standaard op 0 met als commentaar dat enforce zichzelf niet terugverdient.
- `MemoryFlushThreshold` op 80, de broncode-default. Het budget is dit percentage van `MemoryMaxRAM_GB`.
- `MemoryMaxRAM_GB`: ontbreekt de waarde, dan geldt de broncode-default van 64 en rekent GeoDMS op een machine met 128 GB met de helft. Lees bij een zware run het budgetgetal uit het log terug in plaats van het af te leiden.

Met enforce plus een budget van 64 GB liep de allocatie in augustus 2026 reproduceerbaar vast bij de overgang van wonen naar werken: 90 GB gecommit bij een working set van 20 GB en constant 11 procent processorgebruik, dus swappen. Dezelfde variant viel op een tweede machine zonder afgestelde knoppen om op memory allocation errors terwijl hij op de afgestelde machine doorliep.

De knoppen zijn ook per run te zetten, als vlag voor de configuratienaam: `/SQ` en `/CQ` zetten resource scheduling op enforce of uit, `/Sq` op shadow, `/SB<MB>` begrenst het admissiebudget voor deze run en `/CF` schakelt de free-store drainage uit die begint zodra het gebruik boven `MemoryFlushThreshold` komt. De MT_FLAGS uit `RunAll.cmd`, `/S1 /S2 /S3`, zijn de multithreading-vlaggen.

Draai zware runs headless via GeoDmsRun. Een open tabelvenster in de GUI laat de GUI-thread via een timer meedoen aan de update en houdt data resident. Een hangend proces sluit niet af, dus bewaak op loggroei en processorgebruik samen, niet op de exitcode.

## Wis het log voor elke stap

`GeoDmsRun` schrijft met `/L<pad>` naar een bestaand logbestand zonder het eerst leeg te maken. Een script dat na afloop op `[E]` grept vindt dan ook de fouten van de vorige run met datzelfde logpad, en meldt een geslaagde stap als mislukt. Erger: het maakt een echte fout onzichtbaar tussen de oude. Wis het log dus aan het begin van elke stap:

```powershell
if (Test-Path $l) { Remove-Item -LiteralPath $l -Force }
& $Exe "/L$l" '/S1' '/S2' '/S3' $Cfg $Item 2>&1 | Out-Null
```

## Bekende waarschuwingen die geen fout zijn

Een log toets je op `[E]`, maar niet elke `[W]` vraagt om actie. Deze is bekend en mag blijven staan.

`geos_union_polygon` op `SourceData/Landschap/BasiskaartNatuurlijkSysteemNederlandK/geometry` geeft bij elke berekening van dat item 112 regels `GEOS fix failed. fail-reason="Ring Self-intersection"`. De oorzaak zit in de aangeleverde gpkg van de Basiskaart Natuurlijk Systeem Nederland en niet in de configuratie: 132 van de 6.157 polygonen hebben een ring die zichzelf in een punt raakt, het gewone artefact van een 25 meter raster dat naar polygonen is omgezet. GeoDMS repareert er twintig en geeft op de overige 112 op, een regel per polygoon. De raakpunten hebben geen oppervlak; de unie verschilt van een vergridding van de ruwe features op 58 van 56,1 miljoen cellen op 25 meter. Gemeten op 2026-09-10 met GeoDms20.17.0.m; de volledige meting staat in de memory over de BNSN-waarschuwingen.

Laat de bron staan en schoon hem niet op: een reparatie verandert de oppervlakte niet meetbaar en zou een nieuwe vintage van een bronbestand vragen. Komt het aantal regels of de itemnaam anders uit dan hierboven, dan is het wel iets nieuws.

## Trap 2: klopt het (seconden tot minuten)

Een assertie is een `IntegrityCheck` op het onderliggende item, met de exitcode als testuitslag:

```
attribute<float32> Som (Domein) := add(...), IntegrityCheck = "all(abs(this - 1f) < 0.001f)";
```

`IntegrityCheck = "this"` op een parameter die zelf de check is geeft "Invalid Recursion in UpdateMetaInfo". Zet de check dus op de data, niet op de conclusie. Om dezelfde reden mogen IntegrityChecks van parameters niet naar elkaar verwijzen: een volgorde-toets tussen `Model_StartYear`, `Model_FirstZichtjaar` en `Model_FinalYear` staat op een van de drie en niet op alle drie.

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

GeoDmsRun rekent alleen door wat naar een storage gaat. Vraag je een item op met een `StorageName`, dan schrijft hij dat bestand ook echt weg. Wil je alleen toetsen, kies dan een item zonder storage, of een IntegrityCheck; en lees hieronder bij Toetsen terwijl een ander draait waarom dat op zichzelf niet garandeert dat er niets wordt geschreven.

Semantiek van een operator of een randgeval bewijs je het snelst in een losse minimale .dms in de scratchpad, met eigen unitdeclaraties. Neem daar altijd een bewust falende kanarie in op, zodat je weet dat exit 1 ook echt werkt.

### Een gefaalde IntegrityCheck verbergt wat erachter ligt

GeoDmsRun stopt bij de eerste gefaalde IntegrityCheck in de keten van het opgevraagde item. Een run die op zichtjaar N omvalt zegt daarom niets over N+1 tot en met het eind, ook al oogt de melding uitputtend. Op 2026-09-03 viel een harnas om op de legendatoets van Y2090, waarna in een Descr en in een openbaar issue is opgeschreven dat alleen Y2090 het zijbestand miste; het ontbrak bij vier zichtjaren, de andere drie waren nooit bereikt.

Een uitspraak over een reeks vraagt een meting over de hele reeks. Toets de reeks buiten GeoDMS wanneer dat kan, met een `ls` over de standmappen of een lus die elk element apart aanroept. Stel bij elk meetontwerp de vraag welke gevallen deze meting per constructie niet kan zien, en weeg daarnaar hoe luid een waarschuwing moet staan: een val die luid omvalt mag in een Descr, een val die stille onzin oplevert hoort bovenaan het bestand. Dit is de tegenhanger van de val in trap 1: de ene run stopt te vroeg, de andere stopt niet, en in beide gevallen dekt de uitslag minder dan hij lijkt te dekken.

### De zeef kost geen allocatie

Wil je weten wat een zeeftoets per zichtjaar wegzeeft, dan hoef je niet te alloceren. `Templates/VariantData_T.dms` bouwt `container Zeef` als een `for_each` over de zichtjaren, gevoed uit `StateBasisjaar`, de dichtheid, de plancapaciteit en de restricties. De zeef van Y2120 leest de allocatie van Y2110 dus niet, en alle zichtjaren zijn in een aanroep op te vragen. Gemeten op 2026-09-01: alle negen zichtjaren van BAU, twee subsectoren, tien tellingen per zichtjaar, samen 2,5 minuten. Vraag ze in een aanroep op, want zonder CalcCache kost een tweede aanroep de hele basisdata opnieuw.

Bouw zo'n uitdraai als een `Diagnose<nummer>.dms` met een `AsList` over `/Classifications/Time/Zichtjaar/name`, zodat de reeks meebeweegt met `Model_FirstZichtjaar` en `Model_FinalYear`.

Neem een zelftoets op zodra je een samengestelde toets met de hand nabouwt, bijvoorbeeld een OR waar je een term uit wilt laten. Zet de nabouw plus de weggelaten term naast het echte item en schrijf het verschil als kolom weg; staat die kolom niet overal op nul, dan meet je iets anders dan je denkt. Dat houdt de nabouw ook eerlijk wanneer een andere sessie halverwege een term in diezelfde OR vervangt.

## Trap 3: de ketentriggers (minuten)

`CommitChecks` in `cfg/main.dms` dwingt hele deelketens af via ExplicitSuppliers: `MaakBaseData1`, `MaakBaseData2`, `MaakVariantData1`, `MaakVariantData2`, `MaakAllocatieFirstZichtjaar`, plus de drie claimrealisatie-checks. Bedoeld om voor een commit te zien of het model nog loopt, niet voor productie.

`Diagnose.dms` levert de inhoudelijke controlewaarden. Aansturing via de omgevingsvariabelen `DiagCasus` en `DiagJaar`. Zie de skill rs-toetsen voor wat je met die waarden doet.

Die twee werken niet hetzelfde. `DiagCasus` voedt een gewone parameter, dus `WLO_hoog_BAU` volstaat. `DiagJaar` voedt een meta-expressie, dus de waarde moet zelf aanhalingstekens dragen: `'Y2040'` en niet `Y2040`. Zonder die aanhalingstekens wordt het zichtjaar als itemnaam gelezen en krijg je `Unknown identifier 'Y2040'`, een melding die naar het diagnose-item wijst en niet naar de omgevingsvariabele.

Meetharnassen per issue staan als `Diagnose<nummer>.dms` in `cfg/main/Diagnose/`, met een `#include` in de container `PerIssue` onderaan `cfg/main/Diagnose.dms`. Ze zijn tijdelijk en horen weg zodra de getallen in het issue staan. Een nieuw harnas hangt onder `/Diagnose/PerIssue/Diagnose<nummer>/` en niet in de wortel, zodat de bovenste laag van de boom leesbaar blijft; het hoofdharnas blijft `/Diagnose`, dus `/Diagnose/GenerateAll` en `/Diagnose/Casus` zijn onveranderd.

Let bij een nieuw harnas op de naamketen. Een kale naam zoekt vanaf `PerIssue` omhoog en komt dan langs de items van het hoofdharnas voordat hij de wortel bereikt, dus namen als `Casus`, `Jaar`, `Variant` en `Pad_Z` binden aan het hoofdharnas zodra je ze niet zelf definieert. Verwijs naar modelcode daarom met een absoluut pad.

## Trap 4: allocatie draaien

Voor het testen van het allocatiemechanisme hoeft de hele sectorlijst niet mee. Beperk `ModelParameters/SectorAllocRegio` in `cfg/main/ModelParameters.dms` tot de regels die je nodig hebt: commentarieer de rest in `Elements/Text` uit en zet `unit<UInt8> SectorAllocRegio := range(uint8, 0b, <aantal>b)` op het overgebleven aantal. Let op de komma's: de eerste actieve regel heeft geen voorloopkomma, de rest wel. Terugzetten niet vergeten, en kondig zo'n tijdelijke inkorting aan bij de buursessies, want hij is niet committeerbaar.

De uitkomst voor de overgebleven sector is identiek aan die in de volledige run, mits die sector niet van verdringing door de weggelaten sectoren afhangt.

Gemeten rekentijden op zichtjaar 2030, WLO_hoog_NbSGenuanceerd, van voordat de sector Landbouw aanstond en van voor #658 (sinds die commit is 2040 het eerste zichtjaar en bestaat 2030 niet meer; de verhoudingen gelden nog, de absolute tijden zijn een ondergrens):

| Wat | Tijd |
|---|---|
| volledige lijst, zeven regels, sinds de cumulatieve vormtoets van #643 | 72 min |
| alleen Waterberging op Waterbergingsregio | 6,3 min |
| alleen Wonen op NVM | 8 min |
| alleen Werken op NVM, 30 iteraties | 18 min |
| Wonen op NVM plus Waterberging | 12,6 min |
| Diagnose-set met 30 indicatorwaarden, los van de allocatie | 7,3 min |

Een volledig zichtjaar koud herbouwd kost ongeveer 64 minuten: basisdata circa 100 s, variantdata circa 230 s, allocatie circa 3.850 s, indicatoren circa 1.030 s, diagnose circa 460 s.

Twee valkuilen bij het inkorten. `Classifications/Modellering/StandVar_Prep` hangt af van `SectorAllocRegio/Uq_Sectors/HasWerkenSector`, dus zonder werken verdwijnen de banen-standvariabelen en breekt alles wat daarop leunt. En de bestandsnaam van de standtifs bevat `SS-<aantal xSubsectors>`. Dat getal telt de subsectoren van de actieve sectoren: `Classifications/Actor/Sector` wordt opgebouwd uit `SectorAllocRegio/Uq_Sectors/Sectorname`, en `xSubsector` is de union over die sectoren. Commentarieer je een AllocRegio-regel uit terwijl de sector zelf via een andere regel actief blijft, bijvoorbeeld Wonen op COROP terwijl Wonen op NVM blijft staan, dan verandert `Uq_Sectors` niet en blijft de naam gelijk, zodat bestaande tifs vindbaar blijven. Zet je een hele sector aan of uit, dan schuift het getal en zijn de bestaande tifs onbereikbaar, ook voor de indicatorenkant met `StandAllocatieOntkoppeld` op TRUE. Met Landbouw aan, de stand sinds #780, is de naam `SS-26`; zonder Landbouw `SS-11`, want die sector brengt vijftien subsectoren mee. Een sector aan- of uitzetten is dus geen instelling die je vlak voor een levering nog even meeneemt: het is een volledige herberekening van alle varianten en alle zichtjaren.

Voor indicatorcontroles is de allocatie vaak helemaal niet nodig: met `StandAllocatieOntkoppeld` op TRUE leest de indicatorenkant de stand uit de tifs. De batchscripts zetten die omgevingsvariabele; de default in `ModelParameters.dms` is FALSE en geldt alleen voor de GUI en losse aanroepen, dus zet hem zelf bij een losse aanroep.

### Vraag een exportkolom niet via de tabel op

Een item onder `/Indicatoren/<casus>/Zichtjaren/Export/PerNederland/Tabel/...` opvragen trekt de hele tabel en daarmee elke indicator die erin staat: na tien minuten nog niet klaar. De losse `Per_NL`- en `Per_Regio`-items eronder kosten 15 seconden en bewijzen hetzelfde.

Let ook op het pad: de exportcontainer hangt onder `Zichtjaren`, dus `/Indicatoren/<casus>/Zichtjaren/Export/...` en niet `/Indicatoren/<casus>/Export/...`.

## Een variant kan de stand van een andere lenen

De kolom `StandVanVariant` in `cfg/main/VariantParameters/VariantK.dms` zegt uit welke variant de indicatorenkant de standtifs leest. Staat daar de eigen naam, dan alloceert de variant zelf; staat er een andere naam, dan leent hij de stand en hoeft zijn allocatie niet te draaien. De leeskant is precies een plek, `Templates/Indicatoren_T/StandCasus_name`, die `@CASUS@` in `AllocatieFileName` vult; `Variant_rel` blijft die van de lener, dus alle variantparameters worden gewoon van de lener gelezen.

Lenen is alleen geldig als lener en uitlener op alles wat de allocatie raakt gelijk zijn. `Test-LeenAanname` in `batch/Run2120.ps1` bewaakt dat voor de eerste stap: de kolommen waarop de twee verschillen moeten precies de bekende lijst zijn, en de sector Landbouw mag niet in `SectorAllocRegio` staan, want via de landbouwgeschiktheid lopen de droogleggings- en hydrologiekolommen de allocatie in. Lenen is bovendien alleen veilig bij dezelfde `ModelParameters/Skeleton`-instellingen, en daar waarschuwt niets voor.

Stand van zaken: tot 8 september 2026 leende BAU2 de stand van BAU (#730); sinds Landbouw aanstaat (#780) alloceren alle varianten zelf en wijst elke rij van `StandVanVariant` naar zichzelf. Enkele Descr's in `ModelParameters/Advanced.dms`, `Templates/Indicatoren_T.dms` en de kop van `RunAll.cmd` beschrijven nog de leensituatie; de kolom is leidend. Op een LocalData uit de leenperiode ontbreekt de map `Allocatie/WLO_hoog_BAU2`, en dat is dan geen fout: beoordeel die stand bij BAU.

Wat het voor de scripts betekent: `Run2120.ps1` slaat een lenende variant over, eist dat de uitlener in dezelfde aanroep meedraait, en meldt dat in het log. `RunAll.cmd`, `RunZichtjaren.cmd` en `RunScenarios.cmd` kennen het lenen niet en alloceren zo'n variant alsnog. `RunIndicatoren.ps1` hoeft niets te weten, en `ToetsOplevering.ps1` meldt een lenende variant als INFO in plaats van FAIL op een ontbrekende allocatiemap.

## Een productiereeks draaien

### Run2120.ps1, niet RunAll.cmd

Gebruik voor een reeks over alle zichtjaren `batch/Run2120.ps1`. Het script zet `StandAllocatieOntkoppeld` en `VariantDataOntkoppeld` als omgevingsvariabele, verwijdert `LocalDataProjDir` zodat GeoDMS die uit `LocalDataDir` plus de naam van de map boven `cfg` afleidt, haalt de zichtjaren met `@statistics` uit de configuratie, draait basedata, dan variantdata per variant, dan per variant en zichtjaar een eigen GeoDmsRun-proces, en stopt bij de eerste stap met exit 1 of met een `[E]`-regel in het log. Elke stap krijgt een eigen log met tijdstempel en een regel in `batch/log/run2120/status.tsv`; met `-StartBij <stapnaam>` pak je de draad op waar hij bleef, en `-DiagnoseNaZichtjaar` laat het harnas meedraaien zodat de run zijn eigen bewijs achterlaat.

Waarom een proces per zichtjaar: niet de rekentijd maar het geheugen en de herstartbaarheid. Alle zichtjaren in een proces is een veelvoud van de vier waarbij het in augustus 2026 omviel, en bij een val halverwege is nu alleen dat zichtjaar kwijt. `RunAll.cmd` draait met `StandAllocatieOntkoppeld` op FALSE alle zichtjaren in een proces en kan dit niet; hij zet bovendien `LocalDataProjDir` hard, en dat pad moet dan met de naam van de werkkopie meebewegen.

Zichtjaar 2030 doet niet mee: `Model_FirstZichtjaar` staat op 2040 en `Classifications/Time` leidt de reeks daaruit af. De TIGRIS-claim voor 2030 ligt in veel regio's onder de stand van het basisjaar, en omdat het model niet kan slopen om een claim te halen komt daar alleen overrealisatie uit.

Reken op ongeveer 66 minuten per zichtjaar op een rustige machine en tot het dubbele met sessies ernaast; de curve zegt niets over de vordering van de reeks. Vanaf de claimhorizon van 2060 staat de wonen- en werkenclaim stil, dus die blokken alloceren alleen nog wat de opleggingen slopen, maar doorlopen wel alle iteraties. Dat is de eerste plek om te kijken als een reeks korter moet.

Leg voordat je start vast welke build, welke ontkoppelschakelaars en welk LocalData-pad de reeks gebruikt. Geen van die drie staat in de configuratie; zonder die notitie is achteraf niet te zien onder welke instellingen de cijfers zijn ontstaan.

### Start de reeks buiten de sessie

Een batch die je vanuit een Claude-sessie start met `Start-Process` of als achtergrondopdracht hoort bij de procesboom van die sessie. Wordt de sessie herstart, bijvoorbeeld omdat de gebruikslimiet is bereikt of de app opnieuw verbindt, dan ruimt het harnas die boom op en gaan het batchscript en de GeoDmsRun eronder mee; het staplog breekt dan midden in een regel af en `status.tsv` krijgt geen regel voor de stap. Op 2026-09-11 kostte dat een zichtjaar van veertig minuten.

Start een reeks daarom via WMI, zodat het proces onder `WmiPrvSE.exe` hangt en niet onder de sessie:

```powershell
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine      = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<pad>\hervat.ps1"'
  CurrentDirectory = '<werkkopie>'
}
```

Zet de aanroep van `Run2120.ps1` met een `*>`-omleiding naar een consolelog in dat startscript, want `Win32_Process.Create` heeft geen uitvoerkanaal. Controleer daarna dat de `ParentProcessId` van het nieuwe proces bij `WmiPrvSE.exe` hoort. Hetzelfde geldt voor alles wat langer moet leven dan de sessie: een generatiestap van een uur, een reeks diagnoses.

Bewaak zo'n reeks niet op de grootte van het staplog. Windows werkt de mapvermelding van een bestand dat open staat om te schrijven pas bij als de schrijver het sluit of doorspoelt, dus `Get-ChildItem` toont minutenlang een verouderde omvang en een stilstandsdetector op die omvang slaat vals alarm. Meet stilstand op de processortijd van de GeoDmsRun-processen, of lees de echte lengte door het bestand met gedeelde toegang te openen (`[IO.File]::Open(pad, 'Open', 'Read', 'ReadWrite')`), en tel de `[E]`-regels in het log als tweede signaal.

### Tag de codestand

Een productierun beslaat uren en loopt vaak op meerdere machines tegelijk, terwijl de branch ondertussen doorloopt. Zet daarom bij de start een annotated tag op de commit die draait, met de conventie `oplevering_<project>_<datum>`:

```bash
git tag -a oplevering_NL2120_20260829 <commit> -m "..."
git push origin oplevering_NL2120_20260829
```

Zet in de boodschap wat later niet meer te reconstrueren is: welke varianten op welke machines, de zichtjaren, de engine, en de afwijkingen van de standaardopzet. De getagde commit hoeft niet de laatste te zijn die `cfg/` raakte; een commit die alleen `.claude/` of `batch/` wijzigt verandert de berekening niet, maar schrijf dat expliciet in de tag. Wat je niet in de tag zet is wat je niet hebt gecontroleerd: draaien er meerdere machines, dan is `git rev-parse HEAD` op elke machine het bewijs, en zonder dat bewijs hoort er een voorbehoud in de boodschap.

### Ververs de werkkopie niet zolang een reeks loopt

Elke GeoDmsRun-stap laadt de configuratie bij het starten. Een `git pull` in de werkkopie halverwege een reeks laat opeenvolgende stappen daarom op verschillende code draaien, en niets meldt dat. Op 2026-08-27 kwam er tijdens de productierun van #658 een pull binnen, vermoedelijk vanuit Visual Studio: de variantdata van de ene variant was voor de pull geschreven en die van de andere erna.

Moet het toch, bepaal dan eerst per gewijzigd item of het boven of onder de ontkoppellijn ligt. Boven betekent dat een ontkoppeld bestand ervan afhangt: dat bestand opnieuw maken en de allocatie over. Onder betekent dat elke allocatiestap het live rekent en de eerstvolgende stap het vanzelf meeneemt. Dat is per commit anders en aan de bestandsnaam niet te zien. Leg bij een oplevering vast op welke commit elke stap draaide; de tag is het startpunt en `status.tsv` geeft de tijdstippen.

### Een aparte productiekopie bijwerken

Een aparte productiekopie loopt achter zodra de hoofdlijn doorgaat en kan ongecommit werk dragen dat de hoofdlijn al heeft ingehaald. Neem daar nooit een bestand ongezien over; toets per bestand met een drieweg-merge tegen de basis waarop de kopie staat:

```bash
git show "<basis>:<pad>"        | tr -d '\r' > base
git show "origin/NL2120:<pad>"  | tr -d '\r' > ours
tr -d '\r' < "<productiekopie>/<pad>" > theirs
cp ours merged && git merge-file merged base theirs
```

Normaliseer de regeleinden, anders conflicteert het hele bestand op CRLF tegen LF. Wat als toevoeging overblijft is het echte verschil; is dat leeg, dan is de productiekant ingehaald. Een oplevertag die alleen daar staat haal je op met `git fetch <productiekopie> refs/tags/<naam>:refs/tags/<naam>`.

## Meerdere sessies op een machine

In een werkkopie draaien regelmatig meerdere sessies tegelijk, zonder aparte worktrees, en soms met een productiekopie ernaast. Alles in dit kopje volgt uit twee feiten: elke GeoDmsRun-stap parseert de hele configuratie opnieuw, en alle processen op dezelfde `%LocalDataProjDir%` delen de ontkoppelde bestanden.

### Voor je schrijft

Draai `git status` en kijk naar de mtime van de bestanden die je gaat wijzigen, vlak voordat je schrijft. Commit alleen je eigen bestanden met een expliciete `git add`; het recept voor eigen hunks staat in de skill rs-issues.

In een worktree resolvet `%LocalDataProjDir%` naar `%LocalDataDir%/<naam van de map boven cfg>`, waar de ontkoppelde data van het hoofdproject niet staat. End-to-end-tests op dataniveau kunnen daar dus niet. Leg geen junction naar de LocalData van het hoofdproject zonder dat expliciet af te stemmen: dat geeft schrijfrisico in de echte ontkoppelde data.

### Schrijven in cfg terwijl anderen draaien

Een half opgeslagen bestand van een andere sessie is ongeveer een minuut lang dodelijk voor elke stap die in dat venster start. Met veel sessies in een werkkopie is dat een tarief en geen incident.

Schrijverskant: draai de parse-check voordat je de editor verlaat, als onderdeel van het opslaan. `GeoDmsRun.exe "/L<log>" <cfg>\main.dms /ModelParameters/StudyArea` kost drie seconden en vuurt op elk parseerbaar defect in de hele boom; exit 2 is een parse- of laadfout, toets ook op `[E]`. Kondig een bewerking in `Templates/` bij de buursessies aan als hij langer duurt dan een minuut.

Lezerskant: valt jouw run om op een bestand dat je niet herkent, parseer dan eerst opnieuw voordat je gaat uitzoeken. Een controle gaf exit 2 met vijftien foutregels en 57 seconden later exit 0. Meld een parse-fout pas als hij de tweede keer nog staat.

Afstemmen: `ListAgents` toont de buursessies en `SendMessage` bereikt ze rechtstreeks. Doe dat uit jezelf zodra je een buursessie in dezelfde werkkopie ziet, niet pas als er iets omvalt. Meld wat er brak en waarom, vraag hoe lang de ander nog in `cfg/` zit, spreek af dat de ander eerst commit en daarna alleen leest, en zeg wat er in jouw venster naast kan: een diagnosestap van een paar minuten naast een allocatie wel, een tweede allocatie niet. Een sessie die vanuit een eigen scratchpadkopie draait parseert de gedeelde boom niet en bezet het schrijfslot dus niet.

Welke ongecommitte wijziging nog in gebruik is lees je af aan de commandline van de draaiende processen, niet aan de mtime:

```powershell
Get-CimInstance Win32_Process -Filter "Name='GeoDmsRun.exe'" |
  Select-Object ProcessId, CreationDate, CommandLine
```

Die geeft per run het configpad, het item en het logpad, en dat logpad wijst meestal naar de scratchpadmap van de sessie die hem startte. Groepeer daarnaast op mtime: bestanden uit dezelfde minuut zijn een sessie.

### Twee processen op dezelfde LocalData

Draai geen `CommitChecks/MaakBaseData*` of iets anders dat ontkoppelde bestanden genereert zolang een ander GeoDMS-proces op dezelfde `%LocalDataProjDir%` actief is, ook niet met een openstaande GeoDmsGuiQt. De toets is of er uberhaupt een ander proces op die LocalData draait, niet of dat proces het bestand in kwestie schrijft: een lezer is net zo hard geraakt als een schrijver. Draait er iets, herstel dan niet zelf maar meld het en wacht.

De botsing heeft twee gezichten. Schrijvende kant: de generator verwijdert het doelbestand en schrijft het opnieuw; houdt een ander proces het open, dan faalt de delete met `Permission denied`, faalt GDAL op `cannot open dataset` en blijft een stub achter. Volgende runs vallen dan om op de IntegrityCheck van een heel ander item. Lezende kant: een run die het bestand inleest terwijl het net wordt weggeschreven valt om met `gdal Error: Using code not yet in table`. Dat lijkt een fout in een klassificatie, terwijl config en bestand achteraf heel zijn. Gemeten op 2026-08-27: een BBG-tif van 8,2 MB werd teruggeschreven naar 970 KB nullen en een allocatierun van 87 minuten viel erop om. Herstellen is het schrijvende item los opvragen, meestal een halve minuut.

Een generatiestap die door een timeout van de aanroepende sessie wordt afgekapt laat een half geschreven bestand achter dat er goed uitziet: het bestaat, is niet leeg en de header leest. Een controle op lege tifs met een drempel van een paar honderd bytes laat het door. Toets na een afgebroken generatie de omvang tegen een vergelijkbaar bestand (25m tegen 25m) en forceer een echte lees met een aggregatie; het item opvragen raakt alleen de header. Geef generatiestappen en lussen met GeoDmsRun-aanroepen op een gedeelde LocalData een ruime timeout of draai ze in de achtergrond, want wordt zo'n aanroep afgekapt, dan ruimt de harness de procesboom op.

### Nooit op procesnaam opruimen

Een productierun kan uren beslaan en draait vaak naast andere sessies. Ruim GeoDmsRun daarom nooit op naam op:

```powershell
Get-Process -Name GeoDmsRun | Stop-Process -Force   # FOUT
```

Dat raakt elk GeoDmsRun-proces op de machine, ongeacht welke werkkopie eronder draait, en kostte een productierun al eens een zichtjaar en een herstart. Gebruik het PID, of filter op het volledige configuratiepad van je eigen kopie:

```powershell
Get-CimInstance Win32_Process -Filter "Name='GeoDmsRun.exe'" |
  Where-Object { $_.CommandLine -match [regex]::Escape('<werkkopie>\cfg\main.dms') } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Match op het volledige pad tot `cfg` en niet op de mapnaam: een scratchpadkopie heet ook `RSopen_NL2120` en een productiekopie draagt die naam als voorvoegsel, dus een match op de mapnaam raakt ze allemaal en gaf al eens vals alarm over twee scratchpadprocessen met elk een eigen uitvoermap. Of een proces werkelijk in een gedeelde LocalData schrijft zie je aan `AllocatieFileName` in die configuratie of aan de mtimes in de doelmap, niet aan het configuratiepad.

### De processenlijst zegt niet of de baan vrij is

Een reeks diagnosestappen draait elk item als een eigen GeoDmsRun-proces. Tussen twee items zit een gat van een paar seconden waarin er niets draait. Wie op dat moment kijkt ziet een lege lijst en concludeert dat de machine vrij is. Kijk dus naar de mtime van het logbestand van de ander, of vraag het gewoon.

### Toetsen terwijl een ander draait: een losse kopie van cfg

Schrijven in `cfg/` botst met elke lopende reeks GeoDmsRun-stappen. Wachten op een schrijfvenster hoeft niet: de configuratie is 4,5 MB en vrijwel alle databronnen hangen aan `%sourceDataDir%`, dus een kopie doet het net zo goed.

```bash
cp -r cfg Data git.txt /pad/naar/scratchpad/RSopen_NL2120/
```

`Data` en `git.txt` moeten mee omdat vier bronnen aan `%ProjDir%/Data` hangen: de SOMERS-datasheet, de CBS-kerncijfers per wijk en buurt, en twee classificatietabellen. Zonder die map parseert de kopie schoon met exit 0 en valt hij pas om zodra een keten de csv opent, met 49 foutregels op `cannot open dataset`.

De naam van de map boven `cfg` bepaalt waar `%LocalDataProjDir%` heen wijst: `%LocalDataDir%/<naam van de map boven cfg>`. Heet de kopie anders dan het project, dan vindt de configuratie de ontkoppelde bestanden niet; dat valt niet op bij het parsen maar pas als een keten er een leest. Heet hij hetzelfde, dan leest en schrijft de kopie in dezelfde LocalData als de werkkopie. `Run2120.ps1` verwijdert de omgevingsvariabele `LocalDataProjDir` juist om deze afleiding te laten werken; vertrouw op de mapnaam en niet op de variabele om de uitvoer te verleggen.

Op een gedeelde LocalData is een item zonder `StorageName` opvragen niet genoeg om niets te schrijven. Een item zonder storage kan een supplier hebben die er wel een draagt, willekeurig ver de keten in, en GeoDmsRun schrijft elk storage-item dat hij moet uitrekenen. Twee voorbeelden: `SourceData/Grondgebruik/IBIS/Result/RestrictiefWonen` schrijft via de Make-tak een tif zodra een wijziging de fingerprint verandert (vraag een niveau dieper, `Calc_RestrictiefWonen`, dan blijft het lezen), en elke afnemer van de landgebruikskaart leest sinds #803 `LandgebruikskaartNL2120/Write_Result_SA` rechtstreeks, dus die kaart wordt weggeschreven zodra hij wordt uitgerekend, in elk zichtjaar. Een diagnose op een koolstofindicator voor Y2120 liep zo op 2026-09-02 via `PrevIndicatoren` negen zichtjaren terug en schreef tien landgebruikskaarten in een opleveringsmap opnieuw; ze bleken byte-identiek, dus alleen verschoven mtimes. Er is geen veilig zichtjaar: het zichtjaar bepaalt hoeveel kaarten er meekomen, niet of er wordt geschreven. De parameter `ModelParameters/LandUseMapOntkoppeld` staat nog in de configuratie maar stuurt sinds #803 niets meer.

Veiligheid komt van de bestemming van `%LocalDataProjDir%` en van niets anders. Is de uitvoer heilig, zoals een opgeleverde run, geef de map boven `cfg` dan een eigen naam en neem de kosten van het opnieuw maken van de ontkoppelde bestanden voor lief. Kan dat echt niet, behandel de run dan als schrijvend: grep vooraf de keten op `StorageName` en volg elke `:= =` meta-keuze naar de tak die werkelijk wordt gekozen, som de mtimes in de doelmap voor en na op, volg het log tijdens de run op `storage write` zodat je afbreekt in plaats van achteraf ontdekt, en toets gewijzigde bestanden met een hash tegen een schone kopie voordat je iets over schade zegt. Een integriteitscheck op een levering hoort om dezelfde reden op hashes te toetsen en niet op mtimes.

Wil je een uitdraai zien, zet de `StorageName` van dat ene item dan om naar de scratchpad, zodat er niets in de gedeelde `LocalData/Diagnose` belandt terwijl een ander daar schrijft. De kopie is ook de plek om schakelaars om te zetten die in de werkkopie van iemand anders zijn, zoals `IndicatorRegio_ref` op een andere indeling, zonder aan de gedeelde `ModelParameters/Advanced.dms` te komen.

## Een nieuwe restrictie- of stimuliset inlezen

De restrictie- en stimulikaarten die RSopen leest als `SourceData/Restricties/<sector>/<hardheid>` en `SourceData/Stimuli/...` worden niet in RSopen gemaakt. Ze komen uit het aparte GeoDMS-project pbl-nl/model-RS-RuimtelijkeRestricties, eigendom van PBL en los van ObjectVision/RSopen. Hoe dat project is opgebouwd en waar je een laag of hardheid aanpast staat op de wikipagina Restrictie-generatie.

Een nieuwe set in RSopen brengen gaat in vier stappen.

1. Draai het restrictieproject. Het verwacht zijn brondata op `%sourceDataDir%/Ruimtelijke_Restricties`; `sourceDataDir` staat in `HKCU\Software\ObjectVision\<machinenaam>\GeoDMS` en geldt voor alle GeoDMS-projecten tegelijk. Staat de boom een niveau dieper, dan stopt de run meteen op het CBS-gebiedsindelingenbestand en faalt daarmee de hele optelling, dus toets dat pad met `Test-Path` voordat je draait. Het schrijft naar `%LocalDataProjDir%/Output/<tijdstempel>/Restricties_<sector>_<hardheid>.tif`, en de stimuli op dezelfde manier.
2. Kopieer die map met de hand naar `%RSo_DataDir%/Beleid/Restricties/<tijdstempel>/` (stimuli naar `Beleid/Stimuli/`). De share is schrijf-eenmaal: altijd een nieuwe tijdstempelmap, nooit een bestaande overschrijven.
3. Zet `ModelParameters/Restricties_filedate` of `Stimuli_filedate` op de nieuwe tijdstempel en schrijf in de Descr wat er in de set anders is dan in de vorige, met het issuenummer.
4. Laad met trap 1 het item `SourceData/Restricties` en toets het log op `[E]`: `SourceData.dms` bouwt per combinatie uit `Actor/Sector_x_ResHardheidK` een bestandsnaam op, en een ontbrekend bestand kan met exit 0 aflopen.

Let op wat er daarna verouderd is. De standtifs, de indicatoruitvoer en de basisjaarzeef zijn met de oude set gemaakt en hebben bewust geen fingerprint op de set, dus niets waarschuwt. Een andere set vraagt een volledige herberekening voordat een uitkomst iets zegt.
