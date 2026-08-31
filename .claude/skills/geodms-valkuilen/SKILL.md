---
name: geodms-valkuilen
description: Stille fouten in GeoDMS-configuratie die geen foutmelding geven maar wel een verkeerd antwoord; naamafscherming en de kale name, poly2grid-volgorde bij geneste polygonen, PropValue op StorageName, ExplicitSuppliers op een container, null-semantiek, off-grid rasters en een geschiktheid die een spikkelkaart oplevert. Lees dit voordat je DMS-code in RSopen schrijft of wijzigt.
---

# Stille fouten in GeoDMS-configuratie

Alles hieronder is in RSopen daadwerkelijk misgegaan en gaf geen foutmelding. Een exitcode 0 bewijst bij geen van deze gevallen iets. Loop de lijst langs voordat je DMS-code schrijft, en neem bij twijfel een assertie op; zie de skill rs-draaien.

## Naamafscherming

GeoDMS zoekt een ongekwalificeerde naam omhoog vanaf de plek waar het sjabloon STAAT, niet vanaf de plek waar het wordt geinstantieerd. Een subcontainer in `Templates` met een naam die ook elders in de boom bestaat, schermt die daarmee af voor elke ongekwalificeerde verwijzing vanuit een sjabloon.

De oplossing is niet de container hernoemen maar de verwijzing kwalificeren: schrijf vanuit een sjabloon `/BaseData/` en niet `BaseData/`. Alle verwijzingen naar BaseData en SourceData binnen `cfg/main/Templates` staan sinds augustus 2026 met leidende slash.

Uitzondering: verwijzingen die in samengestelde strings zitten zijn niet met een slash te kwalificeren. Daarom staan `PotentieleStates`, `Suitabilities` en `Beschikbaarheden` in het meervoud naast hun enkelvoudige tegenhanger.

## De kale `name` in een subcontainer

Een `parameter<String> name` op templateniveau werkt niet meer binnen een subcontainer die zelf een `name` erft. Voorbeeld: binnen `unit<uint64> CompactedAdminDomain := Geography/CompactedAdminDomain` levert een kale `name` de string `CompactedAdminDomain` op, want die unit heeft zelf een `name`.

Op templateniveau valt dat niet op zolang de eigen-naam-eigenschap toevallig gelijk is aan wat je bedoelt. Gebruik binnen zo'n subcontainer nooit een kale `name`; er staat in `IterSubsector_T` een `parameter<String> Subsector_name` naast `name` voor dit doel.

Dit ging in augustus 2026 op zes plekken mis. Twee harde fouten waarbij de allocatie na 98 s omviel, en een stille: `IsSubsectorZelfVervuilendWerk` stond altijd op FALSE, zodat de omgekeerde milieuzonering nooit heeft gewerkt en nijverheid en logistiek wel door hun eigen buffer werden geweerd.

## poly2grid bij geneste polygonen

`poly2grid` kent per cel een polygoon toe en laat bij overlap de polygoon winnen die als laatste aan de beurt is. Bij een bron met geneste polygonen bepaalt de leesvolgorde dus de uitkomst, zonder waarschuwing.

Meet bij elke vectorbron die op het raster komt eerst of `sum(opp per polygoon)` groter is dan `union_all().area`. Zo ja, dan is er overlap en moet de volgorde expliciet vastliggen. In een `gdal.vect`-SqlString kan dat met `order by ST_Area(geom) desc`, zodat de kleinste polygoon als laatste komt en wint.

Een wijziging in een SqlString kan de volgorde stil veranderen: een window function partitioneert op geom en sorteert daarmee de output. Zo verdween bij #613 stilzwijgend 1.500 van de 12.233 ha, met exitcode 0. Neem bij zo'n wijziging altijd een areaal-assertie op.

`poly2allgrids(polygonen, grid)` is het alternatief: dat geeft een kruistabel met `polygon_rel` en `grid_rel`, waarmee de tie-break expliciet in de config staat. Alleen de moeite waard bij veel echte gedeeltelijke overlap; bij overwegend nesting is `order by ST_Area(geom) desc` goedkoper en even sluitend.

## ExplicitSuppliers op een container

`ExplicitSuppliers` op een CONTAINER lift niet mee wanneer je een los kind opvraagt. Bij `for_each`-containers kun je een schrijfactie dus niet aan de container hangen en erop rekenen dat hij meekomt.

En let op de plaats in de regel. Heeft het item een expressie, dan komen de eigenschappen NA die expressie, achter een komma. `attribute<X> Y (D) : ExplicitSuppliers = "Z" := expr` geeft "item terminator ';' expected after item definition"; `attribute<X> Y (D) := expr, ExplicitSuppliers = "Z";` is goed. Verwar dit niet met een item zonder expressie, zoals een attribuut dat zijn waarde uit een storage haalt: `attribute<X> Y (D) : StorageName = "...", StorageReadOnly = "True";` is de normale vorm en daar staat de dubbele punt wel meteen achter het domein.

## Eenheidsliteralen werken niet overal

`0[Eur]`, `0[Woning]`, `0[meter2]` en `0[Eur_m2]` lossen alleen op waar de eenheidscontainer in scope is, via een `using` op het bestand of via de plek in de boom. In `Diagnose.dms` is dat niet zo: die container heeft geen `using` en hangt niet onder de eenheden. Een meetexpressie die daar een eenheidsliteraal gebruikt faalt met `Unknown identifier 'Eur'`, en dat blijkt pas als je het item opvraagt, niet bij het parsen.

Cast in meetcode daarom naar `float32` en reken met kale getallen:

```
sum(float64(float32(pad/naar/item)))          // in plaats van sum(pad/naar/item)
MakeDefined(float32(pad/naar/opp), 0f) > 0f   // in plaats van MakeDefined(pad/naar/opp, 0[meter2]) > 0[meter2]
```

Je verliest de eenheidscontrole, maar in een uitdraai die toch naar tekst gaat levert die niets op. Zet de eenheid in de kolomnaam, zoals `nietwoon_totaal_mld`.

## De foutregel wijst niet naar de oorzaak

Twee parsefouten waar de melding een regel verderop wijst dan waar het misging.

Een puntkomma na de Descr van een container die daarna nog een blok opent:

```
container X
: Descr = "..." ;     // FOUT: deze puntkomma sluit de container af
{ ... }
```

Dat geeft `item definition or block terminator '}' expected` met de accolade als foutregel, terwijl de puntkomma de oorzaak is. Bij een container met een `for_each` plus een eigen subcontainer komt dezelfde melding.

En een eigenschap voor de toekenning in plaats van erna geeft `item terminator ';' expected after item definition`, met de hele regel als foutregel. Zie de kop over ExplicitSuppliers hierboven.

Parseer daarom na elke handmatige ingreep in een dms-bestand, voordat je een lange reeks start:

```powershell
& $Exe "/L$log" '/S1' '/S2' '/S3' $Cfg '/ModelParameters/StudyArea'
```

Dat kost seconden. Een configuratie die halverwege een reeks stukgaat kost de hele reeks.

## PropValue geeft de expressietekst

`PropValue(item, 'StorageName')` geeft de expressietekst terug, niet de uitkomst. Dat werkt als je hem meteen weer als StorageName gebruikt, maar niet als invoer voor iets dat een echt pad verwacht, zoals `ExistingFile`. Zet het pad dan als eigen `parameter<String>` neer en verwijs daar vanuit beide kanten naar.

## Null-semantiek

`null < x` en `0f/0f < x` geven FALSE. Er is dus geen null-propagatie naar bool, ook niet door `&&` of `OR(...)` heen. Een null-conditie in een `switch` valt door naar de default.

Dat is handig zolang je het weet en een valkuil zodra je aanneemt dat een null zich door een vergelijking heen plant.

Bij rekenen geldt precies het omgekeerde, en dat is de duurdere helft. Een float-null is een NaN en propageert door elke bewerking, ook door een vermenigvuldiging met nul. `float32(FALSE) * null` is dus null en geen nul, en `null + 5` is null. Een vlag voor een factor zetten schakelt die factor niet uit:

```
float32(!IsNuGealloceerd) * StateVoor
+ float32(Allocatie == DezeSubsector) * Dichtheid * Resultaat   // Dichtheid null maakt de hele som null
```

Deze term is de kern van een keten die niets meer teruggeeft dan nulls, terwijl er in de configuratie geen enkele fout zichtbaar is. Wie dezelfde formule als ternaire operator schrijft, heeft het probleem niet: de niet-gekozen tak wordt niet meegenomen, dus daar komt de null nooit binnen. Datzelfde verschil maakt dat twee schrijfwijzen die er equivalent uitzien verschillende antwoorden geven.

Denk hierbij aan de plekken waar de configuratie zelf bewust een null neerzet, zoals `... ? ... : (0f/0f)` op cellen buiten een regiokaart. Zo'n null hoort bij "onbekend hier", maar hij lekt de allocatie in op cellen waar de betreffende term er helemaal niet toe doet. Wikkel de factor in `MakeDefined(..., 0)` of zet hem in een tak, en toets het met een telling van `!IsDefined(...)` over het domein voordat je conclusies trekt.

Beide helften bewijs je in seconden met een losse .dms in de scratchpad; zie de skill rs-draaien, trap 2.

## `float32(x)` houdt de metriek vast, `x[float32]` strijkt hem weg

De twee schrijfwijzen zien er inwisselbaar uit en zijn dat niet. `float32(x)` verandert alleen het waardetype en laat de eenheid staan, `x[float32]` gooit de eenheid weg. Een verhouding die je met `float32()` bouwt draagt dus de eenheden van teller en noemer mee, ook als de declaratie iets anders zegt: de metriek volgt uit de expressie en niet uit het opgegeven waardetype.

Meestal merk je dat pas ver stroomafwaarts, waar de vermenigvuldiging met de doeleenheid botst: "Values mismatch between Base Units of first argument (Job per W) and Base Units of cast target (Job)". De melding wijst naar de plek van de botsing en niet naar de deling die de eenheid meebracht, en die twee kunnen in verschillende bestanden staan.

Gevaarlijker is het geval waarin de eenheden toevallig tegen elkaar wegvallen: dan is er geen melding en klopt het getal alsnog niet. Kies dus bewust. Wil je een dimensieloze verhouding, gebruik `[float32]` op teller en noemer. Wil je dat de eenheden meerekenen, cast dan niet en laat GeoDMS de eenheidsalgebra doen: `Woning_ha` maal `Job/Woning` maal `ha` levert vanzelf `Job`.

Aanleiding 2026-08-28: `Banen_InWoongebied / Woningen_InWoongebied` in `BaseData/VerzorgendBijWonen.dms` was met `float32()` gebouwd en droeg daardoor `Job/Woning` mee, terwijl de declaratie `Float32` zei. De botsing kwam pas boven in `max_elem` in de allocatie, vier minuten rekenen verderop.

## Rasters die niet op het modelraster liggen

GeoDMS leest een raster op georeferentie, niet positioneel, en rondt een niet-gehele celoffset af naar de dichtstbijzijnde cel. Dat gaat goed zolang alle lagen dezelfde afronding krijgen, maar het levert een GridStorageManager-waarschuwing op en het is niet zichtbaar in de uitkomst.

Het recept in RSopen is een `Bron`-container die het originele bestand leest en een `Maak`-container die het als tif op het modelraster wegschrijft, waarna de gewone laagnamen de tif read-only lezen. Toegepast op ABCD, bodemdaling en risicozonering. Bijvangst: 394 MB ASCII werd 3,6 MB tif en de inleestijd ging van 22,5 naar 0,5 s.

Let op dat GeoDMS geen NODATA-tag schrijft. Binnen GeoDMS is de nullwaarde null, maar QGIS en Python tonen hem als gewone waarde. Zet die tag zelf als het bestand buiten GeoDMS gebruikt wordt.

## Een geschiktheid per cel geeft een spikkelkaart

Zet je in een allocatie een trekking per cel als geschiktheid, dan kloppen de arealen en is de kaart onbruikbaar. De allocator maximaliseert de som van de geschiktheid, dus hij pakt de losse toppen van het ruisoppervlak, en die liggen als losse cellen van 25 bij 25 meter door elkaar. Exitcode 0, de opgave gehaald, en toch fout.

De ingreep is de geschiktheid over een schijf te middelen voordat de allocator hem ziet. Dan komen er aaneengesloten gebieden boven de zaaglijn uit in plaats van losse toppen. Toegepast bij waterberging (`Suitability_Zichtjaar_T/Totaal_Geclusterd`, straal 100 m) en bij de natuurallocatie van zand (`SourceData/Grondgebruik/Natuur/.../Zand`, straal 500 m).

Wil je ruis houden zonder spikkels, trek hem dan op een grover raster en middel hem daarna: het gemiddelde van honderd trekkingen ligt zo dicht op een half dat er geen relief overblijft, terwijl het gemiddelde van een handvol vanzelf tussen 0 en 1 blijft zonder normaliseren of afkappen.

Let bij `discrete_alloc_sp` op de taakverdeling tussen de termen. Een term die voor alle typen gelijk is bepaalt welke cellen meedoen, maar valt bij de keuze tussen typen tegen elkaar weg. Welk type een cel wordt hangt dus uitsluitend af van het verschil tussen de typen. Wil je dat de typen als vlekken naast elkaar liggen en niet door elkaar heen, dan moet juist die verschilterm ruimtelijk glad zijn.

Meet het, want met het oog op een uitgezoomde kaart zie je het niet. Het getal dat het vangt is het aandeel buurcellen binnen 50 meter dat dezelfde bestemming krijgt, gemiddeld over de gealloceerde cellen, afgezet tegen wat een willekeurige trekking uit dezelfde zeef zou geven. Bij zand ging dat van 0,19 naar 0,80.

## Er is geen CalcCache meer

De CalcCache, de persistente schijfcache met automatische invalidatie, is verdwenen sinds de GeoDMS 8-serie. Presenteer hem nooit als bestaande voorziening; wiki-pagina's die er in de tegenwoordige tijd over schrijven zijn GeoDMS 7-documentatie.

De huidige praktijk is strategisch ontkoppelen: stabiele tussenresultaten expliciet wegschrijven naar in de configuratie gedeclareerde storages en in een latere run teruglezen. Er is geen automatische invalidatie; het verversen na een wijziging bovenstrooms is een bewuste stap. Zie de skill rs-fingerprints.

De praktische consequentie voor het toetsen: twee items uit dezelfde dure container kosten twee volledige berekeningen. Vraag ze in een aanroep op, met beide paden achter elkaar op de commandoregel, in plaats van in twee stappen na elkaar. Een allocatie van een uur wordt anders een allocatie van twee uur voor twee getallen uit dezelfde container.

## De stand beschrijft niet het bestaande gebruik

De sectorkant van de stand zegt wat er in DIT zichtjaar is gealloceerd, niet wat een cel is. Bestaande bebouwing die niet opnieuw wordt gealloceerd draagt geen sector, terwijl haar landgebruiks- en koolstofklasse wel bebouwd zeggen.

Wil je weten wat een cel is, lees dan de landgebruiks- of koolstofklasse. Wil je weten wat er dit jaar mee is gebeurd, lees dan de sector. Wie de tweede vraag stelt om de eerste te beantwoorden krijgt een antwoord dat er plausibel uitziet.

Het venijn is dat de fout twee kanten op valt en er allebei goed uitziet, zonder foutmelding:

```
IsDefined(Stand/Subsector_rel)                      // te ruim: elke gealloceerde cel, ook waterberging
Sector/IsStedelijk[Stand/Sector_rel]                // te krap: alleen wat dit jaar is gealloceerd
```

Beide zijn in #657 langsgekomen, in dezelfde indicator, binnen een week. De eerste zette in Y2030 15.542 waterbergingscellen op dichtbebouwd. De tweede liet een emissiefactor op ruim 28.000 ha bestaand stedelijk veen landen, waar juist was afgesproken dat stedelijk gebied op nul blijft. De reparatie is een vlag op de klasse, met een IntegrityCheck op de coderange zodat hij niet meeschuift als er een rij in de tabel bij komt, en een toets op klasse OF sector wanneer je zowel het bestaande als het nieuwe wilt vangen.

Zo vang je hem: bouw de meting twee keer langs verschillende wegen en leg de arealen naast elkaar. Hier voorspelde een losse telling uit BOFEK en het basisjaarlandgebruik 44.417 ha terwijl de indicator 72.741 ha gebruikte. Dat gat was het hele bewijs; zonder de tweede weg was er niets geweest om tegenaan te kijken.

## Een uitgeschakelde sector breekt een naamexpansie

De sectorlijst in `ModelParameters/SectorAllocRegio/Elements/Text` bepaalt welke sectoren meedoen. Staat een sector uitgecommentarieerd, dan bestaan zijn afgeleide namen niet: geen `LU_ModelType/V/Verblijfsrecreatie_Totaal`, geen `Subsector/v/Verblijfsrecreatie_Totaal`. Elke `=`-expansie die zo'n naam uit een sectornaam opbouwt valt dan om op Unknown identifier.

Het model vangt dat af met een schakelaar per sector, `Uq_Sectors/Has<Sector>Sector`, in de vorm

	attribute<Bool> IsLU_Verblijfsrecreatie (AdminDomain) :=
		=/ModelParameters/SectorAllocRegio/Uq_Sectors/HasVerblijfsrecreatieSector
			? 'gg_prev == LU_ModelType/V/Verblijfsrecreatie_Totaal'
			: 'const(FALSE, AdminDomain)';

Drie dingen om te weten. Het is een metadata-fout, geen rekenfout, dus hij komt niet boven bij een run die het item niet aanraakt; op 2026-08-29 stond hij in de basisjaar-landgebruikskaart terwijl die kaart al maanden goed werd geexporteerd. Een template kent de schakelaar niet, dus een aanroep die alleen de sectornaam als string doorgeeft ontsnapt aan de guard en moet de schakelaar zelf meekrijgen als parameter. En de guard hoort op elke tussenstap te staan, niet alleen op de uitkomst: `Verharding.dms` had hem wel op zijn resultaten maar niet op `Verhard0` en `Verhard`, en die worden via `Per_NL` en `Per_Regio` wel bereikt.

Zoek ze met een grep op de sectornaam in `=`-expansies, en toets met de sector uit, want met de sector aan is de guard onzichtbaar.

## Een template kan op vier manieren aangeroepen worden

Zoek je uit of een template nog gebruikt wordt, dan zijn letterlijke treffers niet genoeg. Een template kan rechtstreeks worden aangeroepen, via de stringvorm in `for_each_ne`, via een uit stukken opgebouwde naam (`Dairy_T` en `Akkerbouw_T` komen uit `LandbouwKlasses/Templatetype`), en zonder haakjes als `container X : = Vergridding_T { ... }`. Die laatste twee hebben nul letterlijke treffers en draaien wel degelijk.
