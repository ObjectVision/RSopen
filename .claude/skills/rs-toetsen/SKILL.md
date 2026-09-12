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
$env:DiagJaar  = "'Y2040'"
& "<pad naar GeoDmsRun.exe>" "/L$env:TEMP\diag.log" "<werkkopie>\cfg\main.dms" "/Diagnose/GenerateAll"
```

Let op de aanhalingstekens rond het zichtjaar. `Diagnose/Jaar` is een `=`-expressie, dus de waarde van `DiagJaar` komt in een expressiecontext terecht en moet daar een stringliteral zijn. Zonder de binnenste aanhalingstekens faalt de run met "Unknown identifier 'Y2040'". `DiagCasus` heeft ze niet nodig, want dat is een gewone stringparameter.

De tabel `Checks` bepaalt wat er gemeten wordt: per regel een naam, een pad (Z is het zichtjaar van de indicatoren, V is variantdata, A is allocatie), een aggregatie (p parameter, s som over het grid, b aantal cellen waar waar, c aantal gevulde cellen, l lijst per regio, m maximum, n minimum) en het item. Een check toevoegen is een regel in vier lijsten plus `nrofrows` een hoger; loopt dat uit de pas, dan geeft `GenerateAll` exit 1 en schrijft hij niets, zie in geodms-valkuilen het kopje over handmatige lijsten.

De hele set kost ongeveer 7,3 minuten los van de allocatie. Met `StandAllocatieOntkoppeld` op TRUE leest de indicatorenkant de stand uit de tifs en hoeft er niet gealloceerd te worden.

Wat moet sluiten:

- Grondbalans. De arealen per landgebruik tellen op tot het studiegebied. Sluit doorgaans op enkele honderdsten van een procent; alles boven een tiende procent is een bevinding. Een vaste rest van enkele tientallen hectare die niet meeschaalt met het verlies wijst op een bestemming die geen naam heeft, niet op een fout die meeschaalt.
- Claimrealisatie per allocatieregio: `claimreal_NL_*`, `claimreal_NVM_woningen`, `claimreal_Provincie_banen`, `claimreal_Waterberging`. Kijk naar het minimum en het maximum over de regio's, niet naar het landelijke gemiddelde. Een landelijke 1,00 kan tientallen regio's onder de norm verbergen.
- Kruiselings tussen zichtjaren. De sterftecijfers horen over de zichtjaren tot op zeven cijfers te sluiten.
- Decomposities. De sloop valt uiteen in exogeen, gealloceerd en rest; de inbreiding in een teller en een noemer met bruto bij en af. Tellen de delen niet op tot het totaal, dan is er een categorie zoek.
- Gevulde kaarten. Alle weggeschreven kaarten per zichtjaar horen gevuld te zijn, geen enkele leeg of geheel nul. Een lege kaart is een stille fout.
- Tabelsom tegen rastersom. Leg bij een oplevering de som van een weggeschreven kaart naast de som van de bijbehorende tabelkolom; zie Noemer en masker onder Wat een bevinding is.

### Uitdraaien buiten de tabel Checks

Niet alles past in de drie paden Z, V en A. `/Diagnose/Ongemeten/uitdraaiWB` schrijft `Diagnose/piekbuiberging_<casus>_<jaar>.txt`, een regel met gelabelde waarden uit BaseData en het basisjaar; `batch/ToetsOplevering.ps1` leest dat bestand. Hij hangt als ExplicitSupplier aan `GenerateAll`, dus een volledige diagnosedraai maakt hem vanzelf; los opvragen kan met dezelfde omgevingsvariabelen. Reken op ongeveer 5,5 minuut per casus en zichtjaar, waarvan circa 2 minuten en 40 GB voor de ToedelingsMatrix van alle panden.

De regel bevat opgave, aanbod, gedekt, ongedekt en dekkingsgraad, sinds #746 het dakoppervlak gesplitst in plat en schuin voor bestaand gebied en nieuwbouw (`best_dak_plat_mlnm2`, `best_dak_schuin_mlnm2`, `nb_dak_plat_mlnm2`, `nb_dak_schuin_mlnm2`, `nb_daken_werken`) en sinds #757 het aanbod per maatregel. Twee ijkpunten: de opgave is 497,023 mln m3 in elke variant en elk zichtjaar (107,8 mm over 460.879,56 ha bebouwd gebied), en het aanbod van gealloceerde bergingscellen is per constructie nul. Wijkt de opgave af, dan is de maskering of het basisjaar veranderd en niet het aanbod.

Gooi het uitvoerbestand tussen twee losse metingen weg, zodat een oude uitdraai niet voor de nieuwe doorgaat. ToetsOplevering keurt een bestand van voor de runstart af als verouderd, maar een losse meting heeft die bewaking niet.

### Wantrouw een harnas dat ouder is dan de fix

Een meetharnas leest een item onder een kolomnaam, en die naam blijft staan als het item van betekenis verandert. Bij #684 las het harnas een item dat inmiddels de afstand tussen twee leveringen mat in plaats van wat er nog geleegd werd, en de uitdraai suggereerde dat de fix niets deed; rechtstreeks meten op HEAD gaf het tegendeel. Controleer bij een harnas dat ouder is dan de wijziging of het nog hetzelfde item leest, en meet na een dag met meerdere gedragswijzigingen opnieuw voordat je een getal uit een commit message overneemt: commits van dezelfde ochtend kunnen elkaars conditie al hebben verzet.

Een ontbrekende uitdraai telt als GEEN DATA en nooit als PASS. Wat de run niet wegschrijft is achteraf niet te beoordelen zonder opnieuw te rekenen.

## Laag 1b: lees eerst de wikipagina van de indicator

Een getal dat optelt en plausibel oogt kan nog steeds iets anders meten dan je denkt. Elke indicator heeft een eigen wikipagina met wat hij meet, wat hij niet meet, en de aannames die de uitkomst sturen. Lees die voordat je een conclusie trekt, niet erna. Waar de wiki staat en hoe je erin schrijft staat in de skill rs-wiki; `Effectmodules-en-indicatoren.md` is de index en de pagina heet meestal naar de indicator (`Claimrealisatie.md`, `Verharding.md`, `Mortaliteit-agv-groenveranderingen.md`).

De wiki kan achterlopen op de code. Bij een verschil is de code leidend voor wat er is gerekend, en is het verschil zelf een bevinding die op de wiki thuishoort. Oudere pagina's gebruiken nog de variantnamen BAU/WBS/Transformeren in plaats van BAU/BAU2/NbSMax/NbSGenuanceerd.

Vier valkuilen die een verkeerde conclusie opleverden voordat de wiki erbij werd gehaald:

- Claimrealisatie hoort over de schaalniveaus gelezen te worden, niet op NVM alleen. Overflow is asymmetrisch: een tekort schuift omhoog naar COROP en provincie en wordt daar alsnog ingevuld, een overschot blijft staan want het allocatiedoel is `max(restclaim, 0)`. Staan op Y2120 tientallen NVM-regio's onder 0,95 terwijl de provincies alle tussen 0,96 en 1,01 liggen, dan missen die regio's hun claim niet maar herverdeelt de variant woningbouw over regiogrenzen. Zie `Claimrealisatie.md` en `Overflow.md`.
- Zet regio's apart die hun claim al voor de allocatie hadden gehaald. Daar kan de realisatie niet anders dan boven 1 uitkomen. `ClaimRealisatie_Toets` in `Templates/Indicatoren.dms` doet die scheiding en levert tekort, overschot en saldo; het saldo hoort rond nul te liggen. Voor werken wijst de kolom `al_gehaald` in de uitdraai `claimtoets_werken` de regio's aan waar de claim onder de basisjaarstand ligt.
- De piekbui-indicator en de waterbergingssector delen alleen hun naam. De indicator meet de piekbui in bebouwd gebied, de sector alloceert seizoensberging in het landelijk gebied op een eigen claim per bergingsregio. Ze bij elkaar optellen of tegen elkaar afzetten is een categoriefout.
- `CO2Flow_TovBasisjaar` is een klein verschil van twee grote voorraden. De voorraad is ongeveer tweehonderd keer zo groot als het verschil, dus een wijziging van een tiende procent in de zichtjaarvoorraad slaat door als ruim twintig procent in deze indicator. Zet er altijd `CO2Stock_Zichtjaar` en `CO2Ongedekt_Cumulatief` naast, en lees hem niet als maat voor de omvang van een effect.

Let ook op tekenafspraken. `SterfteAfname` is positief wanneer het groen bij woningen toeneemt en de sterfte dus daalt; negatief betekent extra sterfgevallen. De formule is `ReferentieSterfte * NDVIToename * EffectPerNDVI * Bewoners * Periode`, met `EffectPerNDVI` op `0,04 / 0,1` en dus positief.

## Laag 2: orde van grootte

Een getal dat optelt kan nog steeds onzin zijn. Zet elke uitkomst naast een referentie: hetzelfde getal in het vorige zichtjaar, in de vorige ronde, of in de BAU-variant. Springt het meer dan een factor, dan is dat een bevinding tot het tegendeel is aangetoond.

### Referentiewaarden staan op de huidige zichtjarenreeks

Sinds #658 begint de reeks op Y2040 (`ModelParameters/Model_FirstZichtjaar`) en loopt hij door tot Y2120; Y2030 bestaat niet meer. De rondes van voor 29 augustus 2026 (#639) maten Y2030 en een Y2040 dat via 2030 tot stand kwam, terwijl de eerste stap nu zeventien jaar beslaat in plaats van zeven. Die getallen zijn geen voor-en-na-referentie meer, ook de 2040-waarden niet: een verschil ermee komt uit de zichtjarenreeks en niet uit het ontwikkelwerk. Vergelijk een ronde alleen met een ronde die ook op Y2040 begint.

Referentiewaarden op de huidige reeks, gemeten op een stilstaande stand:

- Y2040, toetsronde van 2 september 2026 (#753), BAU en NbSGenuanceerd: piekbuiopgave 497,023 mln m3, claimrealisatie landelijk 1,00065 voor wonen en 1,01857 voor banen, sloop door nieuwe natuur 25.048,03 woningen, en de sluitingstoets van #741 klopt op vier decimalen.
- Y2120, productiereeks van 1 september 2026: claimrealisatie wonen landelijk 0,9953 in BAU en 0,9948 in NbSGenuanceerd, maar regionaal 11 tegen 33 van de 76 NVM-regio's onder de claim; lees dat over de schaalniveaus, zie laag 1b. De waterberging zakt in NbSGenuanceerd op Y2120 naar 0,9256 door verzadiging. BAU en BAU2 zijn op Y2120 identiek op de CO2-kaarten na: de parameters waarin ze verschillen zijn waterbeheer en werken niet door naar de allocatie.

Twee verschijnselen die geen fout zijn maar een claimvraag. Werken schiet door waar de claim onder de basisjaarstand ligt, want het model kan geen banen slopen; `al_gehaald` in `claimtoets_werken` wijst die regio's aan. En de opgelegde natuur is in elk zichtjaar tot op de cel gelijk, want de oplegging is variantdata en gaat in het eerste zichtjaar in een keer op.

Verschuivingen die als normaal gelden bij een enginewijziging, gemeten in augustus 2026: totalen bewegen niet (woningvoorraad plus 0,11 tot 0,44 procent), de plek wel. Nieuwe wooncellen op dezelfde plek 95 tot 99 procent in het eerste zichtjaar en 80 tot 85 procent in het tweede, logistiek 57 procent in het tweede.

Denk bij een grote uitslag eerst na over de rekenrichting voordat je hem als fout bestempelt. Voorbeeld: bij #641 zakte de nieuwe natuur maar 17.191 ha terwijl 43.995 ha gespaard werd. Dat leek een inconsistentie, maar de rest was in het basisjaar al natuur of water. Aangetoond door de twee natuurkaarten cel voor cel te kruisen: 275.063 cellen weg, 27 erbij.

### Drie afbakeningen van het veen

Elk veengetal staat op een van drie oppervlakken, en een uitspraak van Deltares zegt er zelden bij welke. De SOMERS-veenweidepercelen beslaan 245.968 ha. Veen en moerige grond volgens BOFEK2020 beslaan 438.667 ha, waarvan 231.783 ha buiten die percelen. Het peilvakoppervlak van de bouwstenentabel is 671.504 ha, inclusief sloten, erven en bebouwing (664.738 ha na de areaalcorrectie van 10 september 2026). Het gerasterde veengebied van de levering is weer een ander getal: 530.670 ha.

Noem daarom bij elk veengetal op welke afbakening het staat, en vergelijk een kolom uit het areaalblad van team Veen nooit in absolute hectares met een modelgetal. Wie een van de drie voor de andere aanziet leest een tegenspraak waar er geen is, of mist er juist een. De kentallen van team Veen gelden voor het hele peilvakoppervlak en SOMERS rekent op de percelen; dat verschil is precies waarom er kentallen bestaan voor gebied waar het model geen SOMERS-getal heeft.

Twee vallen bij het meten van een nieuwe veenpost. Een post die naast een bestaande komt moet dezelfde schakelaars honoreren; de eerste versie van het kentalregime uit #758 liep om `Koolstof_OxidatieBuitenSOMERSOokHoogNL` heen, waardoor hoog Nederland in de NbS-varianten wel uitstoot kreeg en in BAU niet, 145.000 ha variantverschil dat alleen uit de bedrading kwam. En tel op de tak die de cel werkelijk krijgt en niet op de voorwaarde: een teller op `IsVernatVeenweide` overtelt, want de helft van die percelen is een veenvormende klasse geworden en valt onder een ander kental.

### Kentallen voor de werkenkant

De werkenimplementatie rust op het rapport Ruimte voor werken (SPINlab Research Memorandum SL-20, 2022). Netto ruimtebeslag per baan in 2019: nijverheid 111,8, logistiek 67,2, detailhandel 37,3, overige consumentendiensten 26,7, zakelijke dienstverlening 12,7 en overheid en kwartaire diensten 11,3 m2. Het model realiseert die binnen dertien procent; alleen de basisjaarvoetafdruk van zakelijke dienstverlening (144 procent van de rapportwaarde) en overige consumentendiensten (168 procent) wijkt af. Bruto-netto verhoudingen: ongeveer 11 bij overheid en kwartair, bijna 5 op bedrijfsterrein, 2 bij detailhandel en horeca. Een bebouwde fractie van 9,5 procent bij overheid en kwartair is dus geen anomalie maar die verhouding van 11, en 12.270 ha ruimtebeslag over de reeks tot 2120 is wat 11,3 maal 11 voorspelt (124 m2 bruto per baan tegen 122 in het model). Leg tabel 4 van het rapport, netto ruimtebeslag per sector voor 2019 en 2050 Hoog, naast de gerealiseerde arealen per subsector. Voor de verdunning op bedrijfsterrein meet het rapport sinds 2012 nog 1,3 procent per jaar bij industrie en 1,2 bij logistiek; het model rekent 0,5 en 0,25, en dat is een bewuste keuze en geen afvlakking (zie de Descr van `Groeifactor` in `ModelParameters/Werken.dms`).

### Een gemiddelde over het hele domein is een artefact

De statistiekcontainers per extent (Totaal, BinnenUrbanContour, BuitenUrbanContour) maskeren de extent met een deling door nul. Voor een post die buiten zijn geldigheidsgebied geen zinnige waarde heeft zijn gemiddelde en mediaan over Totaal en BuitenUrbanContour dan onbruikbaar, en een kale `@statistics` over het hele domein evenzeer. Bij de grondproductiekosten gaf `@statistics` voor PlanProces 22,7 miljoen euro per hectare als gemiddelde en Totaal 36.903.900 als mediaan, terwijl de mediaan binnen de kern 251 duizend is (364 duizend voor BouwWoonrijp). Gebruik BinnenUrbanContour, of reken per cel na uit de brontifs.

Die brontifs zijn rechtstreeks met rasterio te lezen en dat is vaak sneller dan een GeoDMS-aanroep. Let op de metadata: `Omgeving/Kaveldichtheid2018.tif` is uint8 op 100 meter, `Omgeving/Reistijd5kInw.tif` is float32 met NaN op 61,5 procent van de cellen en zonder NODATA-tag, dus een kale som telt die NaN's mee.

## IJk een bodemgebruikstabel op de kaart die het model leest

Een tabel per bodemgebruiksklasse, bijvoorbeeld welk deel van elke klasse aan wonen is toegewezen, is alleen iets waard als hij op dezelfde kaart is gemaakt als de zeef. Twee dingen gaan daar stil mis.

De kaart. Het model leest de BBG-jaargang uit `ModelParameters/BBG_Year` via `/BaseData/StartState/Bodemstatistiek/gg_CBS`. Op de share ligt een kant-en-klaar modusraster van een ander jaar, en dat is niet dezelfde kaart: het jaar verschilt en de klassen zijn verschoven omdat busbaan toen nog een actieve rij was. Gemeten op dat raster kwam semi-verhard terrein op 18,5 procent toegewezen en dagrecreatief terrein op 20,9; op gg_CBS is dat 0,2 en 0,6 procent. Het harnas `Diagnose/PerIssue/DiagnoseVerdikking/Kalibratie` schrijft gg_CBS en de plancapaciteit als tif weg, met de klassenamen op indexvolgorde in een zijbestand, zodat je buiten GeoDMS op de juiste kaart rekent.

De index. `Classifications/Grondgebruik/CBSKlasse2020.dms` heeft uitgecommentarieerde regels (busbaan, wrakkenopslagplaatsen, natuurlijk grasland, kustduinen), dus de rasterindex loopt niet gelijk met de EK2020-code en ook niet met de leesvolgorde daarvan. Lees de etiketten uit dat zijbestand en controleer op arealen die je kent: voor Noord-Holland hoort 41.388 ha woonterrein en 111.375 ha IJsselmeer uit te komen. Een tabel met verschoven etiketten valt pas op als een uitgesloten klasse toch een hoog percentage krijgt.

Bouwterrein hoort bovenaan te staan (29,9 procent toegewezen in Y2040 van BAU, gemeten september 2026). Een uitgesloten klasse die daar in de buurt komt wijst op een verkeerde kaart of een verschoven index. Wil je daarna verklaren welke evident-benut-route een cel dichthoudt, kijk dan naar `IsEvidentBenutBinnenPlancapaciteit` en `IsEvidentBenutBuitenPlancapaciteit` in `Zeef_Basisjaar_T`, waar de CBS-lijst en de BGT-tif met een OF samenkomen.

## Landbouw: een claimband van nul bevriest de allocatie

`ModelParameters/Landbouw/claims_conservatief/Claimbandbreedte` staat standaard op 0 en is via de omgevingsvariabele `RSO_CLAIMBANDBREEDTE` te zetten. Bij 0 zijn onder- en bovengrens per landbouwklasse per allocatieregio allebei gelijk aan het basisjaarareaal maal de restclaimfactor. De basisjaarkaart is daarmee zelf een toegestane oplossing met transitiekosten nul op elke cel, en die wint van elke afwijking: `discrete_alloc_sp` levert precies de basisjaarkaart terug, en alleen de restclaim haalt per regio af wat na stad en natuur niet meer past.

Een wijziging aan de landbouwgeschiktheid, de transitiekosten of het saldo toetsen op de allocatie geeft bij band 0 dus altijd geen verschil. Dat leest als een wijziging die niet doorwerkt of als een kapotte toets, terwijl het een eigenschap van de claim is. Bij #202 was `Alloc_Result` na een volledige herbouw van de transitiekostenmatrix byte-identiek; met de band op 0,05 verschoof 4.053 ha. Toets zo'n wijziging daarom op twee dingen:

1. De geschiktheid zelf, per klasse en alleen op landbouwcellen met bodemcode. Het rastergemiddelde uit `@statistics` gaat ook over steden en water en is niet te lezen.
2. De allocatie met `RSO_CLAIMBANDBREEDTE=0.05`, de gevoeligheidsstand waarvoor die omgevingsvariabele bestaat. `cfg/main/Diagnose/Diagnose202.dms` is het voorbeeldharnas.

## Laag 3: ruimtelijke patronen met de RS-testomgeving

De RS-testomgeving is een eigen git-repo naast de werkkopie (`_Tools/RS-testomgeving`). De README daar is leidend voor het gebruik; hieronder staat wat je vooraf moet weten.

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
- Een nulmeting. `rs_compare.py` neemt twee mappen en matcht op relatief pad, dus twee standmappen kunnen er rechtstreeks in. Op twee identieke mappen hoort hij nul verschil te geven (gemeten: 21 vergelijkingen met nul verschil over 145,6 miljoen cellen). Pas daarna weet je dat een verschil dat later uitkomt echt is en niet uit de opstelling komt.

Rekentijden: `rs_indicators.py` kost bijna vijf uur per zichtjaar voor heel Nederland, want het is op een provincie gebouwd. `rs_compare.py` kost 154 s op de standtifs en 856 s op de indicatorkaarten.

## Meet naast de code in plaats van een A/B te draaien

Voor je een voor-en-na-vergelijking opzet: kijk eerst of de oude en de nieuwe toestand niet allebei in de configuratie staan. Dat is vaker zo dan je denkt, want een begrenzing wordt zelden geschreven door de oude regel weg te gooien.

Vijf vormen die zich voordeden:

1. De twee toestanden staan naast elkaar als aparte items. Bij #669 staan `HeeftWonen` en `HeeftWoongebied` in dezelfde container, met een schakelaar die kiest. Het verschil tussen die twee IS wat de wijziging heeft gedaan, en dat is met een som te meten zonder iets om te zetten.
2. De verwijderde toets is na te bouwen uit onderdelen die er nog staan. Bij #670 was `MinimumSubsectorShare` weg, maar de twee sommen waaruit hij bestond niet. Nagebouwd als meetitem dat nergens in hangt, naast de toets die ervoor in de plaats kwam, geeft dat precies het aantal cellen dat de wijziging heeft heropend.
3. Beide takken van een keuze worden toch al uitgerekend. Bij #699 staan de toewijzing voor hoog en voor laag Nederland als twee attributen naast elkaar; de omgekeerde uitkomst is dan even goed te sommeren als de huidige.
4. De oude toets is uit de nieuwe uitkomst terug te rekenen. Bij #734 gaf de nieuwe regel op een ontbrekende waarde geen beperking meer, en de oude uitkomst is dan `nieuw || (eis && !IsDefined(invoer))`. Die regel als extra kolom in het bestaande harnas geeft voor en na in dezelfde aanroep, op dezelfde codestand en met dezelfde invoer.
5. De post gaat lineair het saldo in. Dan is het saldo zonder die post exact het saldo plus de post, en komen beide standen uit een enkele doorrekening. De vraag of de post de locatiekeuze verzet is dan geen tweede allocatierun maar een overlaptelling van twee rangordes: sorteer de kandidaatcellen per ontwikkelpakket op het saldo met en zonder de post, en tel hoeveel van de bovenste twee en vijf procent in beide lijsten staan. `ControleBodemdaling` in `Suitability_Wonen_perOP_T` doet dat voor de bodemdalingskosten (#505): overlap 93,1 procent in de top twee procent en 94,9 in de top vijf, dus de post verzet ongeveer een op de vijftien toplocaties. Lees de omvang van zo'n post altijd naast de spreiding van het saldo (daar p95 van de post 59.909 euro per cel tegen 550.474 euro tussen p50 en p95 van het saldo). De telling zegt iets over de rangorde binnen een pakket en niets over de wedloop tussen pakketten of sectoren; wie dat wil weten moet alsnog draaien.

Dit scheelt niet alleen een run maar is ook zuiverder: bij een A/B verschilt altijd meer dan wat je onderzoekt, hier per constructie niets.

IJk de reconstructie altijd tegen een eerdere losse meting van diezelfde oude toestand, als die er is. Bij #734 kwam de teruggerekende oude stand op 28.136,875 ha uit tegen de 28.137 ha die een week eerder los was gemeten; pas daarmee stond vast dat de nabouw dezelfde vraag beantwoordde. Klopt de ijking niet, dan meet je iets anders dan je denkt, en dat is precies wat een A/B niet had laten zien.

Twee dingen om te controleren als je zo meet. Sommeer je over `AdminDomain`, leg dan een masker op `IsStudyArea`, anders telt de halve Noordzee mee. En reken na of het gemeten verschil klopt met het kental maal de omvang: bij #699 gaf 1,3 ton per hectare maal 118 hectare areaalverschil exact het gemeten verschil in vastlegging, en daarmee stond vast dat de opzoeking de goede rijen raakte.

### Een koolstofniveau narekenen zonder de keten van zichtjaren

De koolstofindicator is een keten over negen zichtjaren, een uur per zichtjaar. Drie niveaus zijn buiten die keten om te bepalen, in seconden tot een kwartier. Dat is de goedkoopste manier om te zien of een niveau uit de kentallen komt in plaats van uit de variant.

- De basisjaarvoorraad per cel is `stock_Y2120` min `stock_FromBaseYear_Y2120` uit de kaarten van een bestaande run, gelezen met `StorageType = "gdal.grid"`. Zet daar de vraag uit de SOMERS-tif naast; het verschil, afgekapt op nul, is de ongedekte oxidatie. Bij #733 kostte dat dertien seconden in plaats van een uur.
- De twee koolstofpools zijn uit de brondata na te bouwen: BOFEK, de SOMERS-percelen, `Peat_thickness`, de GLG en `SourceData/Bodem/BodemKoolstofvoorraad`. IJk de nabouw tegen datzelfde verschil van de twee stockkaarten; bij #736 kwam dat op de SOMERS-percelen op 2,2e-5 Mton uit, dus exact. Daarna zijn maskers, dieptegrenzen en een ondergrens in een aanroep van een kwartier te varieren, alle varianten in een uitdraai. `Peat_thickness` en de GLG zijn 250-meterrasters die op het 25-meterdomein worden gelezen, en `AsList` kan niet halverwege een gewone stringexpressie als meta-expressie beginnen.
- De opbouw van een cel die nooit van klasse verandert is over de hele horizon exact `min(Cmax - startvoorraad, Cseq * horizon)`, niet negatief, te berekenen uit LGN, de bodemkoolstofkaart en de kentallentabel zonder allocatie. Bij #737 reproduceerde dat de gemeten toename per klasse tot op 1,2 procent (165,93 Mton CO2 theorie tegen 167,87 gemeten). Een niveau dat zo na te rekenen is beweegt niet met de variant mee en is een kalibratie, geen uitkomst.

Twee leesregels. Presenteer koolstof als variantverschil en niet als niveau; het niveau verschuift bij elke ronde aan deze indicator, het verschil is robuust. En lees een saldo van een laat zichtjaar nooit zonder `CO2Ongedekt_Cumulatief` ernaast: op 2040 is die post 0,04 Mton en leest als sluitend, cumulatief op 2120 is hij een derde van de SOMERS-uitstoot.

## Een afleiding toetsen tegen de keten die zij vervangt

Vervangt een einde-jaars afleiding een lange keten van iteratielagen, bewijs de gelijkheid dan naast de code en zonder allocatie: een uitdraai die per subsector de verschillen telt draait in ruim twee minuten. Meet drie maten tegelijk en niet alleen het maximum: het grootste absolute verschil per cel, de som van de absolute verschillen tegen de totale weggeschreven waarde als noemer, en het aantal afwijkende cellen gesplitst naar wie de cel won (deze sector, een andere sector, niemand). Bij de pandvoetafdrukken wees het maximum alleen twee keer de verkeerde kant op: eerst leek de afleiding fout terwijl de keten waarden wiste, daarna leek zij goed terwijl zij op door wonen gewonnen cellen dubbel telde.

Twee patronen in het verschil hebben een vaste betekenis. Een verschil dat exact een sentinel is, zoals 999999 plus een echte waarde tot op de float32-resolutie van 0,0625 rond een miljoen, zegt dat de ene kant null draagt en de andere een waarde; `float32(FALSE) * null` geeft in GeoDMS null en geen nul, dus zoek de opzoeking zonder `MakeDefined` in een term die op elke cel wordt uitgerekend. Een verschil dat exact celoppervlak maal een pakketverschil is (12,499992 m2 is 0,0625 ha maal 2000 min 1800,0001) zegt dat beide kanten een ander pakket lezen; vraag dan welke opzoeking eerste-wint en welke laatste-wint.

Een afleiding moet elk geval van de keten spiegelen, ook de uitzonderingen: niet gealloceerd, gewonnen door deze sector, gewonnen door een andere sector, en de behoudtak waarin een verzorgende subsector blijft staan als wonen wint. Een sectorneutrale vlag als `GealloceerdDitZichtjaar` mist dat laatste geval. Schrijft de afleiding een verkeerde waarde in de stand-tif, dan repareert een tweede indicatorenronde niets; alleen een nieuwe allocatie doet dat, en dat is het verschil tussen een half uur en acht uur per variant.

## Een toetsronde opzetten

### Een voor-en-na-vergelijking opzetten

De valkuil is dat er meer verschilt dan wat je onderzoekt. Wat werkte bij de enginevergelijking van augustus 2026:

1. Een aparte worktree op een branch waarin alleen de te onderzoeken bestanden terug zijn gezet naar de oude commit. Al het andere blijft op HEAD.
2. Eigen LocalData per run, met basisdata en variantdata gekopieerd in plaats van opnieuw gerekend, zodat die per constructie identiek zijn.
3. Reken erop dat er plumbing-fixes nodig zijn die geen gedrag veranderen: hernoemde parameters onder hun oude naam terugzetten, verplaatste templates terugverwijzen. Houd scherp welke daarvan wel gedrag zijn. In dat geval was `IterVanafWaarWeAfgewezenCellenUitsluitenInAlloc` er een: die stond op 5 en staat nu op 1, en dat is wel enginegedrag.
4. Checks uit het diagnoseharnas halen die in de oude versie niet kunnen bestaan.

Concreet voor die vergelijking, mocht hij herhaald moeten worden. De basis was `fa161af4` van 4 augustus 2026 en teruggezet waren negen bestanden onder `cfg/main/Templates/Allocatie`: `IterSubsector_T.dms`, `IterSubsector_T_Wind.dms`, `IterSubsector_T_Wonen.dms`, `Iter_Landbouw_T.dms`, `Iter_T/Iter_Allocatie.dms`, `SectorAllocRegio_T.dms`, `SectorAllocRegio_T/Restricties_Dynamisch_Wind.dms`, `Sequence_T.dms` en `Zichtjaar_T.dms`. Drie plumbing-fixes waren nodig: `Buffer_gridcel_T` is naar `Templates/Allocatie/` verhuisd dus de aanroepen in `SectorAllocRegio_T` en `Sequence_T` moesten mee, `IsWoonkern` in `Iter_Allocatie` had een leidende slash nodig, en de allocatieparameters moesten terug in de hoofdcontainer `ModelParameters` omdat ze sindsdien onder `Advanced` staan. De worktree van die vergelijking bestaat niet meer; met deze gegevens is hij opnieuw te bouwen.

Meld altijd expliciet wat je niet getoetst hebt. Bij die vergelijking waren dat de werken-schakelaars afzonderlijk, de NbS-variant en de zeeflaag.

### Scheid het effect van de code van het effect van de allocatie

Een toetsronde over een reeks commits raakt allebei. Dat gaat in twee trappen op dezelfde nieuwe code. Trap 1 vergelijkt oude tegen nieuwe code op een stilstaande stand en meet dus het indicatoreffect. Trap 2 vergelijkt dezelfde nieuwe code op de oude tegen de nieuwe stand en meet dus het allocatie-effect. Daarvoor moeten twee dingen weggezet zijn voordat er iets draait: de standmappen als `Stand<jaar>_vintage<datum>` en de hele map `Diagnose` met `cp -rp`, zie Bewaar de oude uitdraaien en Een oude stand opnieuw doormeten hieronder. Zonder die twee kopieen is er achteraf geen voor-meting meer.

Begin met de goedkoopste stap, de diagnose op een bestaande stand. Bij #753 bleek binnen een minuut dat `/Diagnose/GenerateAll` al twee dagen exit 1 gaf en het toetsharnas over de hele linie GEEN DATA zou hebben gemeld. Toets ook, voordat een allocatie uren gaat draaien, of de indicatorenexport voor een zichtjaar doorloopt, met een los `Generate_Indicatoren` op een bestaande stand; alles wat daar omvalt had de hele run waardeloos gemaakt.

### Bit voor bit toetsen na een verhuizing

Een refactor die de uitkomst niet mag veranderen toets je met een voor-en-na op de geschreven bestanden, niet op steekproeven. Drie dingen maken zo'n toets stil ongeldig; alle drie gemeten bij #779.

1. Het ijkpunt moet op dezelfde commit staan, niet op de laatste draai die toevallig op schijf ligt. Een draai van een dag eerder lag voor een merge en zes commits, en daardoor verschilden 88 van de 579 bestanden, precies het cluster dat aan de landgebruikskaart hangt. Draai dus eerst het onveranderde bestand op de huidige codestand; dat kost een referentiedraai (41 minuten voor een indicatorenexport) en is goedkoper dan een vals verschil uitzoeken.
2. Een hashvergelijking alleen is niet genoeg. Een bestand dat na de wijziging niet meer geschreven wordt blijft als oud bestand staan en komt als gelijk uit de vergelijking. Tel er daarom bij dat elk bestand een tijdstempel na de start van de draai draagt.
3. Een geopackage is per constructie nooit bytegelijk: `gpkg_contents` draagt een `last_change` met het schrijfmoment. Vergelijk die op rijniveau, met een hash per tabel over `select *`. Tifs, csv's en tfw's zijn wel reproduceerbaar; dat is met drie draaien vastgesteld.

Het recept: hash vooraf met `sha256sum` over tif, csv, tfw en gpkg, draai, vergelijk met `sha256sum -c`, tel de verse tijdstempels, en behandel de gpkg apart. Voor waarom exitcode 0 niets bewijst, zie de skill geodms-valkuilen.

### Een doorlichting met onafhankelijke rollen

Voor een brede doorlichting van een sector, dus de hele keten van claim tot indicator en niet een enkele wijziging, werkt een ronde met meerdere rollen beter dan een enkele lezer. De rollen staan als agents in `.claude/agents/` van de repo: woningmarkteconoom, arbeidseconoom, planoloog, grondeconoom, claimanalist, milieukundige en beleidsspiegel voor wonen en werken, en hydroloog, landbouweconoom en stadsecoloog voor de volgende sectoren.

De opzet die in augustus 2026 op wonen en werken werkte (#663, 55 bevindingen):

1. Laat elke rol de sector onafhankelijk doorlichten. De rollen zien elkaars werk niet. Waar twee of drie langs een andere weg op hetzelfde uitkomen is dat het sterkste signaal; acht van de 55 bevindingen waren zulke convergenties en die kwamen bovenaan in de voorgestelde volgorde.
2. Vraag elke rol ook op te schrijven wat hij heeft getoetst en in orde bevonden. Dat deel bleek even bruikbaar als de bevindingen, want het zegt welke delen van de keten een volgende ronde kan overslaan.
3. Elke bevinding met vindplaats in de configuratie en het gemeten getal, zoals onder Wat een bevinding is.
4. Zet het register in een issue: eerst een overzicht met de convergenties en een voorgestelde volgorde, daarna per rol het register. De losse rapporten van de rollen staan in de scratchpad en verdwijnen; het issue is de blijvende plek. Punten die een eigen reparatie vragen krijgen een eigen issue.
5. Begin een volgende ronde bij dat register en niet bij een samenvatting ervan, want bevindingen verouderen zodra er gerepareerd wordt.

### Een A/B-schakelaar die geen bestand hoeft te zijn

Draai je takken vanuit een bevroren kopie van `cfg` en wissel je per tak een heel bestand om, dan mag de behandelversie nooit uit de doelmap komen. Die map draagt de versie van de vorige tak, dus na een afgebroken run staat daar de referentie in, worden beide toggle-bestanden gelijk, en meet je niets terwijl alles doorloopt met exitcode 0. Haal de behandelversie uit de werkkopie en de referentie uit `git show HEAD:`, en zet er een harde toets op:

```powershell
$verschil = (Compare-Object (Get-Content $Ref) (Get-Content $Behandeld)).Count
if ($verschil -eq 0) { throw "referentie en behandeling zijn gelijk, er valt niets te meten" }
```

Dit is dezelfde faalvorm als een toets die per constructie niets kan vinden: die geeft geen fout maar een geruststellend nulverschil. Bij een A/B is nul verschil tussen twee takken dus altijd eerst een verdenking op de opzet, en pas daarna een uitkomst over het model.

Een bevroren kopie werkt verder goed als iemand anders tegelijk in `cfg` zit te editten. Kopieer `cfg` naar een zusterproject; `LocalDataProjDir` is namelijk `LocalDataDir` uit de registersleutel `HKCU\Software\ObjectVision\<machinenaam>\GeoDMS` plus de naam van de projectmap, dus de kopie krijgt vanzelf een eigen lege LocalData. Heet de map boven `cfg` wel gelijk aan het project, dan deelt de kopie de LocalData van het project; zie rs-draaien.

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

Schrijf de verwachting daarom per wijziging op voordat je meet: welk getal moet bewegen, welke kant op en ongeveer hoeveel. Een getal dat beweegt zonder verwachting is een bevinding. Een getal dat niet beweegt terwijl de verwachting zei dat het moest is de gevaarlijkste, want zo ziet een wijziging eruit die niet is aangesloten: een nieuwe indicator zonder regel in de exportlijst, een schakelaar die nergens gelezen wordt, een kaart die blijft staan met een oud bestand eronder. Zulke blokkades geven exit 0 of pas diep in de keten een fout.

Leg de oordelen per wijziging vast in een werklijst in de repo, zoals `_werklijst-714.md` en `_werklijst-724.md`, zodat hij met de configuratie meevertakt. Vier oordelen: geslaagd, gezakt, zwak (een getal zonder referentie) en open (geen meetpunt). Open betekent zelden tijdgebrek en meestal dat er geen meetpunt bestaat; een nieuw meetpunt in het diagnoseharnas kost ongeveer een kwartier schrijven en een minuut rekenen en maakt de wijziging voorgoed meetbaar. Zet in de kop van de werklijst op welke codestand de oordelen gelden.

### Noemer en masker

Drie toetsregels die elk terugkomen zodra een getal een aandeel, een uitval of een landelijk totaal is. Voor de codekant (teller en noemer op hetzelfde masker) zie de skill geodms-valkuilen.

Een aandeel zonder noemer is geen uitkomst. Zeg bij elk oppervlakteaandeel welk gebied de noemer is: het studiegebied op 25 meter (`CompactedAdminDomain`, 56.146.816 cellen, 35.092 km2), het allocatiedomein, alleen het beschikbare areaal, of alleen de cellen met bebouwing. Bij #669 stond 54,8 procent in de issuetekst en gaf een herhaalde meting op dezelfde regel 65,1 procent; het verschil zat volledig in de noemer, en zonder die erbij leest zo'n herhaling als een tegenspraak. Zet naast het aandeel altijd een absolute maat die niet met de noemer meebeweegt, daar de harde plancapaciteit industrieterrein (4.320 tegen 4.328 hectare op de twee metingen).

Een bruto getal dat niet strookt met het netto effect is een meetfout tot het tegendeel is aangetoond. Alle posten in het exploitatiesaldo van wonen worden vermenigvuldigd met `IsBeschikbaar_zichtjaar` (#597), zodat een cel die voor de sector niet beschikbaar is saldo 0 heeft. Ontbreekt die maskering bij een post, dan krijgt elke niet-beschikbare cel een saldo van precies min die post, en telt de zeefpoort `Impl/ExploitatieSaldo` in `Zeef_Wonen_perOP_T` die cel als saldo-uitval. De allocatie merkt daar niets van, want `Beschikbaar_voorOP` toetst daarnaast op `Beschikbaar_src`; elke meting op de zeefpoort meet dan de sectorbeschikbaarheid en niet de economie. Bij #787 mat de grondprijs zo 204.000 hectare uitval op de saldopoort en tegelijk 6 hectare verschil in het woonareaal; na de maskering was de uitval 0,5 tot 1,0 procent. Twee controles: draagt een nieuwe post in `Suitability_Wonen_perOP_T` dezelfde maskering als zijn buren (kijk in de expressie, niet alleen in de Descr), en zet een uitvalgetal op een zeefpoort tegen het aantal beschikbare cellen voor die subsector en niet tegen het hele domein.

Tabelsom en rastersom meten niet hetzelfde. De tabellen in RegionaleIndicatoren sommeren een weggeschreven kaart per regio; de kaart zelf is gemaskeerd op het studiegebied (`IsStudyArea_AdminDomain`), de tabel op de regio-indeling, en een cel die wel in het studiegebied ligt maar geen regio draagt valt stil uit elke kolom. Het Diagnose-harnas telt met aggregatiecode s over het hele AdminDomain en ziet dat gat niet. Op een voorraad is een gat van een paar duizend hectare verwaarloosbaar; een residu-indicator is een klein verschil tussen twee grote getallen en daar telt hetzelfde gat vele malen zwaarder (op BAU 2120 miste `CO2Stock_Zichtjaar` 0,08 procent en `CO2Flow_TovBasisjaar` 3,7 procent, voordat #748 de toewijzing verfijnde). Sinds #748 lezen de indicatorensjablonen `Per_AdminDomain_Fijn`, dezelfde geometrie op dezelfde resolutie als het kaartmasker, en is het resolutiegat voor NL, Provincie, NVM en COROP nul. Twee verschillen blijven en zijn dekking, geen artefact: de gemeentelijke indeling dekt 3.836,81 hectare studiegebied niet, en de landschapsindeling laat 15.394,56 hectare grote wateren bewust buiten het indelingsgebied. Vraag daarom bij elk landelijk getal of het uit de tabel of uit de kaart komt, en leg bij een oplevering de rastersom naast de tabelsom; verschillen ze op een indeling die het studiegebied dekt, dan is de toewijzing of het masker veranderd en niet de indicator. Er staat nog geen controle voor in de configuratie of in `batch/ToetsOplevering.ps1` (open punt bij #748).

## Bewaar de oude uitdraaien voordat je opnieuw meet

`/Diagnose/GenerateAll` schrijft elke uitdraai onder een vaste naam en overschrijft dus de vorige. Wie een voor-en-na wil, kopieert de map eerst; achteraf is de oude waarde weg en blijft alleen over wat er toevallig in een commit message of een issue staat.

```bash
cp -rp "$LocalDataProjDir/Diagnose" <scratchpad>/diagnose_voor
```

Gebruik `cp -p` en niet een kale `cp`. Zonder `-p` krijgt de kopie de tijd van nu, en juist de mtime is wat de vintage van de baseline bepaalt. Het zijbestand `<naam>.xml` naast elke uitdraai draagt een `SessionStartTime` en een volledige `git status`, dus daaruit is de codestand alsnog te herleiden; kopieer daarom altijd de xml mee.

En kopieer voordat je de nieuwe run start. Een run die al draait heeft de eerste uitdraaien al overschreven, precies de goedkoopste metingen die als eerste klaar zijn.

Twee dingen bepalen of een voor-en-na iets waard is. De stand moet tussen beide metingen stil hebben gestaan, want anders meet je code en allocatie door elkaar. Dat is te controleren op de mtime van de tifs onder `Allocatie/<casus>/Stand<jaar>/`. En de baseline moet te dateren zijn: zoek in de oude waarden een getal dat elders is vastgelegd, in een issue of in een commit message, en pin daarmee vast wanneer hij gemaakt is.

Vergelijk nooit tegen een diagnosebestand van een andere datum zonder de codestand ervan te kennen. Bij #681 schoof de basis twee keer weg terwijl de meting liep, door #700 en door #680, #684 en #724 samen, zodat een verschil dat aan de nieuwe regel werd toegeschreven voor een deel uit die andere commits kwam. Draai beide standen op dezelfde codestand achter elkaar, of pin de baseline met een getal dat in een issue of commit message staat.

## Een oude stand opnieuw doormeten

Naast de uitdraaien staan onder `Allocatie/<casus>/` ook bewaarde standen, met namen als `StandY2040_vintage20260902pre`. Daarmee is een meting die alleen op de oude stand bestond alsnog te herhalen, en dat is meer waard dan het oude getal zelf: je kunt er nieuwe uitsplitsingen op loslaten die er destijds niet waren.

De haak is `ModelParameters/Advanced/AllocatieFileName`. Zet in een scratchpadkopie `Stand@JAAR@` om naar `Stand@JAAR@_vintage<datum>` en de hele indicatorenkant leest de bewaarde stand. Werkt alleen voor de zichtjaren waarvan die map bestaat, dus vraag er precies een op; het basisjaar loopt niet via deze parameter maar via `BaseData/StartState/StateBasisjaar` en blijft dus ongemoeid.

Wat je dan meet is een oude stand onder de huidige code, en dat is precies de combinatie die een vintageverschil zichtbaar maakt. Bij #766 leverde dat het antwoord op de vraag die in het issue nog openstond: van de 2.872 ha gealloceerde waterberging in de stand van 31 augustus stond er 1.662 ha op de landgebruikskaart, en de ontbrekende 1.210 ha werd afgevangen door de opleggingscase. Op de stand van 2 september, uit dezelfde reeks als de basisdata, was datzelfde getal 0 ha. Zonder de bewaarde stand was dat niet meer vast te stellen geweest.

Twee regels die bij zulke metingen op de landgebruikskaart gelden. Een teller op de opleggingsroute is een vintagemelder: de zeef houdt via `Zeef_T/IsRestrictief_DoorExogeenopleggen` elke sector weg van opgelegde cellen, dus zo'n teller boven nul betekent dat de standtifs achterlopen op de oplegging, niet dat de kaartregel fout is. En toets een wijziging in de kaartswitch niet via een `_SA`-kaart, want die leest de weggeschreven tif en niet de verse switch; bij #766 liet dat verschil dezelfde toestand als 2 ha en als 59,4 ha zien.

## Ruimtelijke patronen zonder het model: de standtifs zelf lezen

De RS-testomgeving vergelijkt twee runs op bestandsniveau. Wil je een uitkomst per subsector uitsplitsen, dan kan dat rechtstreeks op `Allocatie/<casus>/Stand<jaar>/`, in numpy, zonder GeoDMS en zonder herdraai. Dat leverde de hele werkareaalvraag op in ongeveer twintig minuten rekentijd.

Wat er ligt en wat het betekent:

- `SubSector_rel_<gebied>_SS-<n>.tif`, uint8, 255 is null. Alleen cellen die het model heeft toegewezen; de basisjaarvoorraad staat er niet in. Eerste-wint over de zichtjaren, dus het getal in Y2120 is de cumulatieve allocatie sinds het basisjaar en het verschil tussen twee zichtjaren is wat er in die periode bij kwam.
- De indexering is de unie uit `Classifications/Actor/Sector/xSubsector`, in de volgorde van `ModelParameters/SectorAllocRegio/Uq_Sectors`. Bij de NL2120-opzet: 0 tot en met 3 wonen (WP2xVSSH, met WP2 het snelst lopend), 4 tot en met 9 werken in Jobs6-volgorde (Nijverheid, Logistiek, Detailhandel, Ov_consumentendiensten, Zak_dienstverlening, Overheid_kw_diensten), 10 waterberging. De `SS-11` in de bestandsnaam is het aantal subsectoren en is dus de controle op die telling; een sector aan- of uitzetten verzet dat nummer en maakt bestaande standen onbruikbaar.
- IJk de indexering voordat je hem gebruikt: kruis elke index met de zes `Werken/<naam>.tif`. Op de cellen van index k hoort de baanstand van subsector k in bijna honderd procent van de gevallen groter dan nul te zijn en die van de andere vijf laag. Gemeten kwam dat op 0,987 tot 1,000 tegen 0,002 tot 0,181.
- `Werken/<naam>.tif` is de volledige baanstand per cel, basisjaar plus nieuw, niet de toename. `PandFootprint/<naam>.tif` idem voor de voetafdruk in m2. Delen geeft m2 per baan; dat maal de dichtheid per hectare geeft de bebouwde fractie van de cel, en dat is de maat die zegt of een subsector zuinig met zijn grond omgaat.

Voor de vraag waar iets landt is `kaarten_basisjaar/Landgebruikskaart_Basisjaar.tif` de goede referentie: klasse 0 is wonen en 1 is werken, en het bestand is bit voor bit gelijk in alle leveringen, dus het is over runs heen vergelijkbaar. Toets dat met een md5 voordat je erop bouwt.

Gebruik de kaart `Verstedelijking.tif` niet om twee runs te vergelijken. Die leest `UrbanContour`, en #749 heeft die begrenzing tussen de leveringen van augustus en september veranderd van de CBS-bevolkingskernen van 2011 naar de eigen afleiding met peiljaar 2022. Het aandeel buiten de contour verschuift daardoor om definitieredenen.

Beter is een afstandsprofiel: `scipy.ndimage.distance_transform_edt` op het complement van de bebouwde basisjaarcellen, en dan per subsector een histogram over afstandsbanden. Daaruit is elke drempel achteraf af te lezen, waaronder de 250 meter waarmee de voorrangstrede voor verzorgend werken werkt (`ModelParameters/Werken/VerzorgendWoongebiedStraal`). Reken de EDT op 50 meter en herhaal hem per strook naar 25 meter: een float64-EDT op het volle raster van 13.000 bij 11.200 kost ruim een gigabyte, en dat kun je niet nemen terwijl er een productierun draait.

Twee laatste dingen. Kijk voor je begint met `Get-Process` of er een GeoDmsRun loopt en hoeveel geheugen die heeft; een allocatie kan tientallen gigabytes vasthouden en dan blijft er weinig over. En de bestanden staan op de Nextcloud-share, dus de eerste lezing is traag en de tweede niet; plan de metingen zo dat je elke tif eenmaal opent.
