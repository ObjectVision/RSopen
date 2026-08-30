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

Dit scheelt niet alleen een run maar is ook zuiverder: bij een A/B verschilt altijd meer dan wat je onderzoekt, hier per constructie niets.

Twee dingen om te controleren als je zo meet. Sommeer je over `AdminDomain`, leg dan een masker op `IsStudyArea`, anders telt de halve Noordzee mee. En reken na of het gemeten verschil klopt met het kental maal de omvang: bij #699 gaf 1,3 ton per hectare maal 118 hectare areaalverschil exact het gemeten verschil in vastlegging, en daarmee stond vast dat de opzoeking de goede rijen raakte.

## Een voor-en-na-vergelijking opzetten

De valkuil is dat er meer verschilt dan wat je onderzoekt. Wat werkte bij de enginevergelijking van augustus 2026:

1. Een aparte worktree op een branch waarin alleen de te onderzoeken bestanden terug zijn gezet naar de oude commit. Al het andere blijft op HEAD.
2. Eigen LocalData per run, met basisdata en variantdata gekopieerd in plaats van opnieuw gerekend, zodat die per constructie identiek zijn.
3. Reken erop dat er plumbing-fixes nodig zijn die geen gedrag veranderen: hernoemde parameters onder hun oude naam terugzetten, verplaatste templates terugverwijzen. Houd scherp welke daarvan wel gedrag zijn. In dat geval was `IterVanafWaarWeAfgewezenCellenUitsluitenInAlloc` er een: die stond op 5 en staat nu op 1, en dat is wel enginegedrag.
4. Checks uit het diagnoseharnas halen die in de oude versie niet kunnen bestaan.

Meld altijd expliciet wat je niet getoetst hebt. Bij die vergelijking waren dat de werken-schakelaars afzonderlijk, de NbS-variant en de zeeflaag.

## Wat een bevinding is

Meld een uitkomst pas als bevinding wanneer je kunt zeggen welk getal je verwachtte en waarom. Een verschil zonder verwachting is een waarneming, geen bevinding. Noem bij elke bevinding het gemeten getal, de referentie en het pad in de config, zodat het na te rekenen is. Een holle OK is geen uitkomst: is een controle niet gedraaid, zeg dat dan.
