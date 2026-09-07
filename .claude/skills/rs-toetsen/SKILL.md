---
name: rs-toetsen
description: Inhoudelijk toetsen of een RSopen-uitkomst klopt; interne consistentie via het Diagnose-harnas, randtotalen en claimrealisatie, orde van grootte tegen referentiewaarden, en ruimtelijke patronen via de RS-testomgeving met rs_compare, rs_report en rs_indicators. Gebruik na een doorgerekende run, bij een voor-en-na-vergelijking en bij twijfel of een getal plausibel is.
---

# Inhoudelijk toetsen van RSopen-uitkomsten

Draaien zonder foutmelding zegt niets over of het antwoord klopt. Toets in drie lagen, in deze volgorde. Sla geen laag over: een ruimtelijk patroon analyseren terwijl de grondbalans niet sluit is verspilde moeite.

| Laag | Vraag | Kosten |
|---|---|---|
| 1 interne consistentie | telt het op, sluit het kruiselings | minuten |
| 2 orde van grootte | is dit getal plausibel | minuten |
| 3 ruimtelijk patroon | staat het op de goede plek | uren |

Zie de skill rs-draaien voor het daadwerkelijk doorrekenen.

## Laag 1: interne consistentie via het Diagnose-harnas

`cfg/main/Diagnose.dms` schrijft een set controlewaarden naar losse tekstbestanden in `%LocalDataProjDir%/Diagnose/`, met de casus en het zichtjaar in de bestandsnaam. Aansturing via de omgevingsvariabelen `DiagCasus` en `DiagJaar`:

```powershell
$env:DiagCasus = "WLO_hoog_NbSGenuanceerd"
$env:DiagJaar  = "'Y2030'"
& "C:\Program Files\ObjectVision\GeoDms20.17.0.m\GeoDmsRun.exe" "/L$env:TEMP\diag.log" "C:\ProjDir\RSopen_NL2120\cfg\main.dms" "/Diagnose/GenerateAll"
```

Let op de aanhalingstekens rond het zichtjaar. `Diagnose/Jaar` is een `=`-expressie, dus de waarde van `DiagJaar` komt in een expressiecontext terecht en moet daar een stringliteral zijn. Zonder de binnenste aanhalingstekens faalt de run met "Unknown identifier 'Y2030'". `DiagCasus` heeft ze niet nodig, want dat is een gewone stringparameter.

De tabel `Checks` bepaalt wat er gemeten wordt: per regel een naam, een pad (Z is het zichtjaar van de indicatoren, V is variantdata, A is allocatie), een aggregatie (p parameter, s som over het grid, b aantal cellen waar waar, c aantal gevulde cellen, l lijst per regio, m maximum, n minimum) en het item. Een check toevoegen is een regel in vier lijsten, meer niet.

De hele set kost ongeveer 7,3 minuten los van de allocatie. Met `StandAllocatieOntkoppeld` op TRUE, de default, leest de indicatorenkant de stand uit de tifs en hoeft er niet gealloceerd te worden.

Wat moet sluiten:

- Grondbalans. De arealen per landgebruik tellen op tot het studiegebied. Sloot op 0,024 procent (2030) en 0,031 procent (2040). Alles boven een tiende procent is een bevinding.
- Claimrealisatie per allocatieregio: `claimreal_NL_*`, `claimreal_NVM_woningen`, `claimreal_Provincie_banen`, `claimreal_Waterberging`. Kijk naar het minimum en het maximum over de regio's, niet naar het landelijke gemiddelde. Een landelijke 1,00 kan negen regio's onder de norm verbergen.
- Kruiselings tussen zichtjaren. De sterftecijfers hoorden over de zichtjaren tot op zeven cijfers te sluiten.
- Decomposities. De sloop valt uiteen in exogeen, gealloceerd en rest; de inbreiding in een teller en een noemer met bruto bij en af. Tellen de delen niet op tot het totaal, dan is er een categorie zoek.
- Gevulde kaarten. Alle 96 gepaarde kaarten per zichtjaar horen gevuld te zijn. Een lege kaart is een stille fout.

## Laag 1b: lees eerst de wikipagina van de indicator

Een getal dat optelt en plausibel oogt kan nog steeds iets anders meten dan je denkt. Elke indicator
heeft een eigen wikipagina met wat hij meet, wat hij niet meet, en de aannames die de uitkomst sturen.
Lees die voordat je een conclusie trekt, niet erna.

De wiki staat als lokale kloon in `C:\ProjDir\_Tools\RSopen.wiki`, markdown, met
`Effectmodules-en-indicatoren.md` als index en `_Sidebar.md` als navigatie. De pagina heet meestal
naar de indicator: `Claimrealisatie.md`, `Verharding.md`, `Mortaliteit-agv-groenveranderingen.md`.

De wiki kan achterlopen op de code. Bij een verschil is de code leidend voor wat er is gerekend, en
is het verschil zelf een bevinding die op de wiki thuishoort. Twee bekende achterstanden: de
variantnamen op oudere pagina's zijn nog BAU/WBS/Transformeren in plaats van BAU/BAU2/NbSMax/
NbSGenuanceerd, en `Overstromingsschade.md` is een stub terwijl de SSM2017-implementatie uitgebreid is.

Vier valkuilen die op 2026-09-01 een verkeerde conclusie opleverden voordat de wiki erbij werd gehaald:

- **Claimrealisatie hoort over de schaalniveaus gelezen te worden, niet op NVM alleen.** Overflow is
  asymmetrisch: een tekort schuift omhoog naar COROP en provincie en wordt daar alsnog ingevuld, een
  overschot blijft staan want het allocatiedoel is `max(restclaim, 0)`. Gemeten op Y2120: bij
  NbSGenuanceerd staan 17 van de 76 NVM-regio's onder 0,95, op COROP nog 6, op provincie nul, met
  alles tussen 0,96 en 1,01. De juiste conclusie is niet dat regio's hun claim missen maar dat de
  variant woningbouw over regiogrenzen herverdeelt. Zie `Claimrealisatie.md` en `Overflow.md`.
- **Zet regio's apart die hun claim al voor de allocatie hadden gehaald.** Daar kan de realisatie niet
  anders dan boven 1 uitkomen. `ClaimRealisatie_Toets` in `Templates/Indicatoren.dms` doet die
  scheiding en levert tekort, overschot en saldo; het saldo hoort rond nul te liggen.
- **De waterbergingsindicator en de waterbergingssector delen alleen hun naam.** De indicator meet de
  piekbui in bebouwd gebied, de sector alloceert seizoensberging in het landelijk gebied op een eigen
  claim per bergingsregio. Ze bij elkaar optellen of tegen elkaar afzetten is een categoriefout.
- **`CO2Flow_TovBasisjaar` is een klein verschil van twee grote voorraden.** De voorraad is ongeveer
  tweehonderd keer zo groot als het verschil, dus een wijziging van een tiende procent in de
  zichtjaarvoorraad slaat door als ruim twintig procent in deze indicator. Zet er altijd
  `CO2Stock_Zichtjaar` naast, en lees hem niet als maat voor de omvang van een effect.

Let ook op tekenafspraken. `SterfteAfname` is positief wanneer het groen bij woningen toeneemt en de
sterfte dus daalt; negatief betekent extra sterfgevallen. De formule is
`ReferentieSterfte * NDVIToename * EffectPerNDVI * Bewoners * Periode`, met `EffectPerNDVI` op
`0,04 / 0,1` en dus positief.

## Laag 2: orde van grootte

Een getal dat optelt kan nog steeds onzin zijn. Zet elke uitkomst naast een referentie: hetzelfde getal in het vorige zichtjaar, in de vorige ronde, of in de BAU-variant. Springt het meer dan een factor, dan is dat een bevinding tot het tegendeel is aangetoond.

Referentiewaarden uit de controleronde van 24 en 25 augustus 2026, casus WLO_hoog_NbSGenuanceerd:

- Wonen haalt in 2030 in elke NVM-regio de claim, minimum 0,9873.
- Werken schiet landelijk door: 1,0625 in 2030 en 1,0489 in 2040. Vrijwel geheel toe te schrijven aan Zak_dienstverlening, waar de claim voor 2030 (1.952.821) onder de basisjaarstand (1.984.240) ligt. Het model kan geen banen slopen, dus daar kan alleen overschrijding uit komen. Dat is een claimvraag en geen allocatiefout.
- Waterberging haalt zijn opgave.
- De opgelegde natuur is in 2040 tot op de cel gelijk aan 2030: 654.854,4 ha en 20.004.318 cellen. Het landschapstoekomstbeeld wordt in een keer in het eerste zichtjaar opgelegd.

Verschuivingen die als normaal gelden bij een enginewijziging, gemeten in de vergelijking van augustus 2026: totalen bewegen niet (woningvoorraad plus 0,11 tot 0,44 procent), de plek wel. Nieuwe wooncellen op dezelfde plek 95 tot 99 procent in 2030 en 80 tot 85 procent in 2040, logistiek 57 procent in 2040.

Denk bij een grote uitslag eerst na over de rekenrichting voordat je hem als fout bestempelt. Voorbeeld: bij #641 zakte de nieuwe natuur maar 17.191 ha terwijl 43.995 ha gespaard werd. Dat leek een inconsistentie, maar de rest was in het basisjaar al natuur of water. Aangetoond door de twee natuurkaarten cel voor cel te kruisen: 275.063 cellen weg, 27 erbij.

## Laag 3: ruimtelijke patronen met de RS-testomgeving

`C:\ProjDir\_Tools\RS-testomgeving`, een eigen git-repo. De README daar is leidend voor het gebruik; hieronder staat wat je vooraf moet weten.

Het instrument vergelijkt buiten het model om, in Python op de geexporteerde bestanden, zodat ook oude commits meedoen die geen nieuwe meet-API kunnen bevatten. Meting en oordeel zijn gescheiden: het meten schrijft ruwe getallen in json, het rapport velt het oordeel op instelbare toleranties. Toleranties bijstellen kost dus alleen een nieuw rapport, geen nieuwe run.

Onderdeel 1, de revision-runner (`main.py`, `Start.bat`), is in revisie en werkt nu niet. Onderdeel 2 werkt.

```
python rs_compare.py <run_a> <run_b> --out cmp --name-a voor --name-b na --only "*StandY2040*" --report
python rs_report.py cmp/compare.result.json --tolerances tolerances.json
python rs_indicators.py --run-a <run_a> --run-b <run_b> --buurt buurt.tif --zichtjaar Y2040 --out ind
```

`rs_indicators.py` levert twaalf figuren op CBS-buurtniveau: woninggroei per buurt met Spearman en outlier-labels, nieuwe wooncellen, verdichtingsaandeel, dichtheid uitbreiding, verdichtingsintensiteit, in- en uitbreidingsdecompositie, Lorenz en Gini, clustergrootteverdeling, randdichtheid en lintaandeel, leapfrog-afstand tot bestaand bebouwd, en banengroei met werkclusterverdeling.

Wat je vooraf moet regelen:

- Beide runs op hetzelfde grid, dus dezelfde bbox en resolutie. Staan ze dat niet, dan valt `rs_compare` terug op aggregatie naar een gemeenschappelijk 100m-raster. Dat is een noodgreep met detailverlies; trek liever de grids gelijk.
- Resultaatbestanden krijgen wel een StudyArea-suffix maar geen commit-suffix. Geef elke run dus zijn eigen `LocalDataDir`, of kopieer de exports tussen runs weg.
- Het buurt-grid komt uit de config: exporteer `/SourceData/RegioIndelingen/Buurt/Per_AdminDomain`. GeoDMS zet daar geen nodata-tag op, dus die moet je zelf zetten, anders telt de zee als een reuzenbuurt mee.
- Python 3.10 of hoger met numpy, tifffile, pillow, imagecodecs en scipy.

Rekentijden: `rs_indicators.py` kost bijna vijf uur per zichtjaar voor heel Nederland, want het is op een provincie gebouwd. `rs_compare.py` kost 154 s op de standtifs en 856 s op de indicatorkaarten.

## Meet naast de code in plaats van een A/B te draaien

Voor je een voor-en-na-vergelijking opzet: kijk eerst of de oude en de nieuwe toestand niet allebei in de configuratie staan. Dat is vaker zo dan je denkt, want een begrenzing wordt zelden geschreven door de oude regel weg te gooien.

Drie vormen die zich in augustus 2026 voordeden:

1. De twee toestanden staan naast elkaar als aparte items. Bij #669 staan `HeeftWonen` en `HeeftWoongebied` in dezelfde container, met een schakelaar die kiest. Het verschil tussen die twee IS wat de wijziging heeft gedaan, en dat is met een som te meten zonder iets om te zetten.
2. De verwijderde toets is na te bouwen uit onderdelen die er nog staan. Bij #670 was `MinimumSubsectorShare` weg, maar de twee sommen waaruit hij bestond niet. Nagebouwd als meetitem dat nergens in hangt, naast de toets die ervoor in de plaats kwam, geeft dat precies het aantal cellen dat de wijziging heeft heropend.
3. Beide takken van een keuze worden toch al uitgerekend. Bij #699 staan de toewijzing voor hoog en voor laag Nederland als twee attributen naast elkaar; de omgekeerde uitkomst is dan even goed te sommeren als de huidige.
4. De oude toets is uit de nieuwe uitkomst terug te rekenen. Bij #734 gaf de nieuwe regel op een ontbrekende waarde geen beperking meer, en de oude uitkomst is dan `nieuw || (eis && !IsDefined(invoer))`. Die regel als extra kolom in het bestaande harnas geeft voor en na in dezelfde aanroep, op dezelfde codestand en met dezelfde invoer.

Dit scheelt niet alleen een run maar is ook zuiverder: bij een A/B verschilt altijd meer dan wat je onderzoekt, hier per constructie niets.

IJk de reconstructie altijd tegen een eerdere losse meting van diezelfde oude toestand, als die er is. Bij #734 kwam de teruggerekende oude stand op 28.136,875 ha uit tegen de 28.137 ha die een week eerder los was gemeten; pas daarmee stond vast dat de nabouw dezelfde vraag beantwoordde, en pas daarna waren de nieuwe getallen te vertrouwen zonder herdraai. Klopt de ijking niet, dan meet je iets anders dan je denkt, en dat is precies wat een A/B niet had laten zien.

Twee dingen om te controleren als je zo meet. Sommeer je over `AdminDomain`, leg dan een masker op `IsStudyArea`, anders telt de halve Noordzee mee. En reken na of het gemeten verschil klopt met het kental maal de omvang: bij #699 gaf 1,3 ton per hectare maal 118 hectare areaalverschil exact het gemeten verschil in vastlegging, en daarmee stond vast dat de opzoeking de goede rijen raakte.

## Een voor-en-na-vergelijking opzetten

De valkuil is dat er meer verschilt dan wat je onderzoekt. Wat werkte bij de enginevergelijking van augustus 2026:

1. Een aparte worktree op een branch waarin alleen de te onderzoeken bestanden terug zijn gezet naar de oude commit. Al het andere blijft op HEAD.
2. Eigen LocalData per run, met basisdata en variantdata gekopieerd in plaats van opnieuw gerekend, zodat die per constructie identiek zijn.
3. Reken erop dat er plumbing-fixes nodig zijn die geen gedrag veranderen: hernoemde parameters onder hun oude naam terugzetten, verplaatste templates terugverwijzen. Houd scherp welke daarvan wel gedrag zijn. In dat geval was `IterVanafWaarWeAfgewezenCellenUitsluitenInAlloc` er een: die stond op 5 en staat nu op 1, en dat is wel enginegedrag.
4. Checks uit het diagnoseharnas halen die in de oude versie niet kunnen bestaan.

Concreet voor die vergelijking, mocht hij herhaald moeten worden. De basis was `fa161af4` van 4 augustus 2026 en teruggezet waren negen bestanden onder `cfg/main/Templates/Allocatie`: `IterSubsector_T.dms`, `IterSubsector_T_Wind.dms`, `IterSubsector_T_Wonen.dms`, `Iter_Landbouw_T.dms`, `Iter_T/Iter_Allocatie.dms`, `SectorAllocRegio_T.dms`, `SectorAllocRegio_T/Restricties_Dynamisch_Wind.dms`, `Sequence_T.dms` en `Zichtjaar_T.dms`. Drie plumbing-fixes waren nodig: `Buffer_gridcel_T` is naar `Templates/Allocatie/` verhuisd dus de aanroepen in `SectorAllocRegio_T` en `Sequence_T` moesten mee, `IsWoonkern` in `Iter_Allocatie` had een leidende slash nodig, en de allocatieparameters moesten terug in de hoofdcontainer `ModelParameters` omdat ze sindsdien onder `Advanced` staan. De worktree van die vergelijking bestaat niet meer; met deze gegevens is hij opnieuw te bouwen.

Meld altijd expliciet wat je niet getoetst hebt. Bij die vergelijking waren dat de werken-schakelaars afzonderlijk, de NbS-variant en de zeeflaag.

## Een A/B-schakelaar die geen bestand hoeft te zijn

Draai je takken vanuit een bevroren kopie van `cfg` en wissel je per tak een heel bestand om, dan mag de behandelversie nooit uit de doelmap komen. Die map draagt de versie van de vorige tak, dus na een afgebroken run staat daar de referentie in, worden beide toggle-bestanden gelijk, en meet je niets terwijl alles doorloopt met exitcode 0. Haal de behandelversie uit de werkkopie en de referentie uit `git show HEAD:`, en zet er een harde toets op:

```powershell
$verschil = (Compare-Object (Get-Content $Ref) (Get-Content $Behandeld)).Count
if ($verschil -eq 0) { throw "referentie en behandeling zijn gelijk, er valt niets te meten" }
```

Dit is dezelfde faalvorm als de kanarie uit `harnas-dat-niemand-aanroept`: een toets die per constructie niets kan vinden geeft geen fout maar een geruststellend nulverschil. Bij een A/B is nul verschil tussen twee takken dus altijd eerst een verdenking op de opzet, en pas daarna een uitkomst over het model.

Een bevroren kopie werkt verder goed als iemand anders tegelijk in `cfg` zit te editten. Kopieer `cfg` naar een zusterproject; `LocalDataProjDir` is namelijk `LocalDataDir` uit de registersleutel `HKCU:\SOFTWARE\ObjectVision\OVSRV08\GeoDMS` plus de naam van de projectmap, dus de kopie krijgt vanzelf een eigen lege LocalData.

Maak van die LocalData geen junction naar de echte in zijn geheel. Dan deel je namelijk ook de allocatiemap, en zodra iemand een standtif in de GUI open heeft valt je run om met `Permission denied` bij het wegschrijven, na alle rekentijd. Maak in plaats daarvan een echte map met junctions per onderdeel, en laat alleen de uitvoer lokaal:

```powershell
foreach ($m in @('BaseData','VariantData','Vastgoed','Indicatoren','Diagnose')) {
    New-Item -ItemType Junction -Path (Join-Path $LD $m) -Target (Join-Path $Bron $m) | Out-Null
}
New-Item -ItemType Directory -Path (Join-Path $LD 'Allocatie')
```

Wil je een bestaande junction opheffen, gebruik dan `[IO.Directory]::Delete($pad, $false)` en nooit `Remove-Item -Recurse`: dat laatste kan door het reparse point heen de echte LocalData opruimen.

## Wat een bevinding is

Meld een uitkomst pas als bevinding wanneer je kunt zeggen welk getal je verwachtte en waarom. Een verschil zonder verwachting is een waarneming, geen bevinding. Noem bij elke bevinding het gemeten getal, de referentie en het pad in de config, zodat het na te rekenen is. Een holle OK is geen uitkomst: is een controle niet gedraaid, zeg dat dan.

## Bewaar de oude uitdraaien voordat je opnieuw meet

`/Diagnose/GenerateAll` schrijft elke uitdraai onder een vaste naam en overschrijft dus de vorige. Wie een voor-en-na wil, kopieert de map eerst; achteraf is de oude waarde weg en blijft alleen over wat er toevallig in een commit message of een issue staat.

```bash
cp -rp /c/LocalData/RSopen_NL2120/Diagnose /pad/naar/scratchpad/diagnose_voor
```

Gebruik `cp -p` en niet een kale `cp`. Zonder `-p` krijgt de kopie de tijd van nu, en juist de mtime is wat de vintage van de baseline bepaalt. Op 2026-09-02 kostte dat het bewijs van welke codestand de baseline had gemaakt; het zijbestand `<naam>.xml` naast elke uitdraai draagt gelukkig een `SessionStartTime` en een volledige `git status`, dus daaruit was het alsnog te herleiden. Kopieer daarom altijd de xml mee.

En kopieer voordat je de nieuwe run start. Een run die al draait heeft de eerste uitdraaien al overschreven; op 2026-09-02 waren dat er acht van de 46, precies de goedkoopste metingen die als eerste klaar zijn.

Twee dingen bepalen of een voor-en-na iets waard is. De stand moet tussen beide metingen stil hebben gestaan, want anders meet je code en allocatie door elkaar. Dat is te controleren op de mtime van de tifs onder `Allocatie/<casus>/Stand<jaar>/`. En de baseline moet te dateren zijn: zoek in de oude waarden een getal dat elders is vastgelegd, in een issue of in een commit message, en pin daarmee vast wanneer hij gemaakt is.

## Een oude stand opnieuw doormeten

Naast de uitdraaien staan onder `Allocatie/<casus>/` ook bewaarde standen, met namen als
`StandY2040_vintage20260902pre`. Daarmee is een meting die alleen op de oude stand bestond alsnog te
herhalen, en dat is meer waard dan het oude getal zelf: je kunt er nieuwe uitsplitsingen op loslaten die
er destijds niet waren.

De haak is `ModelParameters/Advanced/AllocatieFileName`. Zet in een scratchpadkopie `Stand@JAAR@` om naar
`Stand@JAAR@_vintage<datum>` en de hele indicatorenkant leest de bewaarde stand. Werkt alleen voor de
zichtjaren waarvan die map bestaat, dus vraag er precies een op; het basisjaar loopt niet via deze
parameter maar via `BaseData/StartState/StateBasisjaar` en blijft dus ongemoeid.

Wat je dan meet is een oude stand onder de huidige code, en dat is precies de combinatie die een
vintageverschil zichtbaar maakt. Bij #766 leverde dat het antwoord op de vraag die in het issue nog
openstond: van de 2.872 ha gealloceerde waterberging in de stand van 31 augustus stond er 1.662 ha op de
landgebruikskaart, en de ontbrekende 1.210 ha werd afgevangen door de opleggingscase. Op de stand van
2 september, uit dezelfde reeks als de basisdata, was datzelfde getal 0 ha. Zonder de bewaarde stand was
dat niet meer vast te stellen geweest.

## Ruimtelijke patronen zonder het model: de standtifs zelf lezen

De RS-testomgeving vergelijkt twee runs op bestandsniveau. Wil je een uitkomst per subsector uitsplitsen,
dan kan dat rechtstreeks op `Allocatie/<casus>/Stand<jaar>/`, in numpy, zonder GeoDMS en zonder herdraai.
Op 2026-09-05 leverde dat de hele werkareaalvraag op in ongeveer twintig minuten rekentijd.

Wat er ligt en wat het betekent:

- `SubSector_rel_<gebied>_SS-<n>.tif`, uint8, 255 is null. Alleen cellen die het model heeft toegewezen;
  de basisjaarvoorraad staat er niet in. Eerste-wint over de zichtjaren, dus het getal in Y2120 is de
  cumulatieve allocatie sinds het basisjaar en het verschil tussen twee zichtjaren is wat er in die
  periode bij kwam.
- De indexering is de unie uit `Classifications/Actor/Sector/xSubsector`, in de volgorde van
  `ModelParameters/SectorAllocRegio/Uq_Sectors`. Bij de NL2120-opzet: 0 tot en met 3 wonen
  (WP2xVSSH, met WP2 het snelst lopend), 4 tot en met 9 werken in Jobs6-volgorde (Nijverheid, Logistiek,
  Detailhandel, Ov_consumentendiensten, Zak_dienstverlening, Overheid_kw_diensten), 10 waterberging. De
  `SS-11` in de bestandsnaam is het aantal subsectoren en is dus de controle op die telling.
- IJk de indexering voordat je hem gebruikt: kruis elke index met de zes `Werken/<naam>.tif`. Op de cellen
  van index k hoort de baanstand van subsector k in bijna honderd procent van de gevallen groter dan nul
  te zijn en die van de andere vijf laag. Gemeten kwam dat op 0,987 tot 1,000 tegen 0,002 tot 0,181.
- `Werken/<naam>.tif` is de volledige baanstand per cel, basisjaar plus nieuw, niet de toename.
  `PandFootprint/<naam>.tif` idem voor de voetafdruk in m2. Delen geeft m2 per baan; dat maal de
  dichtheid per hectare geeft de bebouwde fractie van de cel, en dat is de maat die zegt of een subsector
  zuinig met zijn grond omgaat.

Voor de vraag waar iets landt is `kaarten_basisjaar/Landgebruikskaart_Basisjaar.tif` de goede referentie:
klasse 0 is wonen en 1 is werken, en het bestand is bit voor bit gelijk in alle leveringen, dus het is
over runs heen vergelijkbaar. Toets dat met een md5 voordat je erop bouwt.

Gebruik de kaart `Verstedelijking.tif` niet om twee runs te vergelijken. Die leest `UrbanContour`, en
#749 heeft die begrenzing tussen de leveringen van augustus en september veranderd van de
CBS-bevolkingskernen van 2011 naar de eigen afleiding met peiljaar 2022. Het aandeel buiten de contour
verschuift daardoor om definitieredenen.

Beter is een afstandsprofiel: `scipy.ndimage.distance_transform_edt` op het complement van de bebouwde
basisjaarcellen, en dan per subsector een histogram over afstandsbanden. Daaruit is elke drempel achteraf
af te lezen, waaronder de 250 meter waarmee de voorrangstrede voor verzorgend werken werkt
(`ModelParameters/Werken/VerzorgendWoongebiedStraal`). Reken de EDT op 50 meter en herhaal hem per
strook naar 25 meter: een float64-EDT op het volle raster van 13.000 bij 11.200 kost ruim een gigabyte,
en dat kun je niet nemen terwijl er een productierun draait.

Twee laatste dingen. Kijk voor je begint met `Get-Process` of er een GeoDmsRun loopt en hoeveel geheugen
die heeft; op 5 september stond er een op 69 GB en was er 4 GB vrij. En de bestanden staan op de
Nextcloud-share, dus de eerste lezing is traag en de tweede niet; plan de metingen zo dat je elke tif
eenmaal opent.
