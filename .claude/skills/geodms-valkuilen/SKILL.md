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

## Een StorageName die niemand opvraagt schrijft niets

GeoDmsRun rekent alleen door wat wordt opgevraagd en naar een storage gaat. Een item met een `StorageName` dat in geen enkele `Generate`-lijst voorkomt bestaat dus wel in de boom, maar het bestand ontstaat nooit. Er komt geen waarschuwing, want er is niets mis: niemand heeft erom gevraagd.

Dat is anders dan de valkuil hierboven. Daar staat het kind onder een container die wel wordt opgevraagd en lift de eigenschap niet mee; hier staat het kind helemaal niet in de lijst.

Gebeurd bij `#721`. `WriteStand/Legenda` schreef het zijbestand met de standlegenda en was correct gedefinieerd, maar `Impl/Generate` had `ExplicitSuppliers = "=asList('WriteStand/'+StandVar/path, ';')+Extra_str"`, en `Legenda` is geen StandVar en zat ook niet in `Extra_str`. Gevolg: over twintig standmappen nul zijbestanden, terwijl de leeskant een stand zonder kloppend zijbestand hard weigert. Het eerste zichtjaar schreef nog, het tweede brak, en de hele ontkoppelde indicatorenkant lag stil.

De controle is goedkoop en hoort bij elke nieuwe `StorageName`: grep of het itempad ergens in een `ExplicitSuppliers` of een `Generate` voorkomt. Staat het er niet, dan schrijft het nooit. En de kanarie achteraf is simpeler nog: kijk of het bestand na een run werkelijk op schijf staat.

## Een IntegrityCheck dwingt geen schrijfactie af

Wie het vorige geval wil repareren grijpt al snel naar een `IntegrityCheck`, want dat is bij een `for_each` de enige haak per item: de checkArray. En aan de leeskant is bekend dat een check een sibling met leesstorage wel degelijk afdwingt.

Voor een SCHRIJFstorage werkt dat niet. Gemeten in een losse dms op 2026-09-01, GeoDms20.17.0.m, met een schone uitvoermap:

| geval | wat er staat | exit | tif | zijbestand |
|---|---|---|---|---|
| A | `IntegrityCheck` op het tif-item noemt `strlen(Legenda) > 0` | 0 | ja | nee |
| C | zelfde check, drempel op `> 1000`, als kanarie | 1 | ja | nee |
| D | de legenda staat in de expressie van het tif-item | 0 | ja | ja |
| E | een afnemer een laag hoger leest het tif-item en de legenda | 0 | ja | ja |

Geval C bewijst dat de check in A wel wordt geevalueerd en de waarde van de sibling echt wordt uitgerekend; het bestand ontstaat alleen niet. Rechtstreeks om het item vragen levert het bestand meteen op, dus aan de storage mankeert niets.

De regel: een schrijfstorage vuurt op de datagraaf en niet op de checkgraaf. Wil je een bestand op schijf hebben, zorg dan dat het item als data in de keten zit of expliciet in een `ExplicitSuppliers` of een `Generate` staat. Een check erop is geen vervanging.

Zo ging het bij `#732`. De stand-tifs van de tussenliggende zichtjaren kwamen er wel, want die zijn supplier van het volgende zichtjaar, en het legenda-zijbestand niet, want dat hangt aan geen enkele StandVar. De reparatie zit daarom in `Extra_prev` in `Zichtjaar_T`: elk zichtjaar noemt het `Generate` van zijn voorganger in zijn eigen `ExplicitSuppliers`.

Twee eigenschappen van `ExplicitSuppliers` die daarbij bleken, en die nergens in de documentatie staan. Een supplierpad wordt omhoog gezocht vanaf de container van het item en niet relatief genavigeerd: `../../Y2040/Impl/Generate` geeft `ExplicitSupplier not found`, het ongekwalificeerde `Y2040/Impl/Generate` werkt. En de ketting draagt door: wijst Y2050 naar Y2040 en Y2040 naar Y2030, dan levert een aanroep van alleen Y2050 alle drie de bestanden op.

## Een uitdraai die niet meedraait blijft stil staan

Hetzelfde mechanisme, maar dan verraderlijker, want hier is er wel een bestand: alleen een oud.

`/Diagnose/GenerateAll` heeft `ExplicitSuppliers = "=AsList('Resultaten/'+Checks/name+'/Waarde', ';')"` en dwingt dus alleen de regels uit de tabel `Checks` af. De losse parameters in datzelfde bestand vallen erbuiten. Ze schrijven naar dezelfde map, dragen sinds `#692` wel de casus en het zichtjaar in de naam maar geen tijdstempel, en blijven na een verse ronde gewoon staan zoals ze waren.

Op 31 augustus 2026 ging dat twee keer bijna mis. `grondbalans_bestemmingen` gaf 437,5 ha waterberging op vruchtbare landbouwgrond terwijl de verse uitdraai op nul stond, en `waterberging_perregio` toonde voor BAU een opgave van 28,7 miljoen m3 die `#664` net had afgeschaft. Beide bestanden waren uren oud en van een andere codestand. Wie ze naast de verse getallen legt vindt een tegenspraak die er niet is, of concludeert dat een wijziging niet werkt terwijl hij wel werkt.

Controleer daarom bij elke aflezing de mtime tegen het tijdstip van je eigen run, ook als de rest van de map er vers uitziet.

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

### Een vergelijking omdraaien klapt de betekenis van null om

Omdat `null < x` en `null > x` allebei FALSE geven, betekent een null in een wegzeeftoets iets anders dan in een voldoettoets. `diepte > Max` zeeft op null niets weg; `diepte <= Max` laat op null niets toe. De ene vorm leest een ontbrekende waarde als geen beperking, de andere als niets is toegestaan, en het herschrijven van de ene naar de andere ziet eruit als een logisch equivalente ombouw.

Zo ging het bij #723, dat de dieptetoets van de zeef omdraaide naar een voldoettoets per bouwwijze. Op de 20.864 ha binnen de gevaarzone waar de LIWO-kaarten geen waarde geven viel daarna elke bouwwijze af en sloot de zeef alle woningbouw uit, terwijl de kostenkant diezelfde cellen met een `MakeDefined` op nul meter bleef lezen. Exitcode 0, geen waarschuwing, en het stond ruim een week in een oplevering. Gerepareerd in #734 met een `MakeDefined` in het sjabloon zelf, zodat de afspraak op een plek staat.

Draai je een vergelijking om, stel dan expliciet vast wat er op een null hoort te gebeuren, en schrijf dat als `MakeDefined` of als een aparte `IsNull`-tak op. Twee dingen om te weten bij het beoordelen hoe ver zo'n fout reikt. Een toets die op een null voor elke variant faalt is onafhankelijk van de maskers en de drempels eromheen, dus latere wijzigingen daaraan veranderen de uitkomst niet en de fout reikt terug tot de commit die de vergelijking omdraaide. En de nullen zitten zelden waar je ze zoekt: hier kwamen ze niet uit de brondata maar uit een plausibiliteitsklem die onzinwaarden op null zet.

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

## Overerving van een container is early binding

`container B := A { ... }` erft de items van A en laat je er items aan toevoegen of overschrijven. Een GEERFD item houdt echter de verwijzing naar het item uit A, ook als je dat item in B overschrijft.

Gemeten op 2026-09-01, GeoDms20.17.0.m:

```
container src            { Blad := TRUE;  Afgeleid := !Blad; }
container src_zonder := src { Blad := FALSE; }
```

`src_zonder/Blad` is FALSE, zoals bedoeld, maar `src_zonder/Afgeleid` blijft FALSE en wordt geen TRUE: het leest `Blad` van `src`. Alleen de items die je zelf noemt volgen de override, en er komt geen waarschuwing.

De consequentie is dat je elk item moet noemen dat je wilt verleggen, ook de afgeleide. Bij `Trede/src_ZonderPlancapaciteit` in #739 zijn dat alle 57 plancapaciteitsvlaggen en niet alleen de zeven die rechtstreeks uit SourceData lezen; de dertig Buiten-vlaggen zijn afgeleiden van de Binnen-vlaggen en zouden anders stil de oude waarde houden. Genereer zo'n lijst uit de bron in plaats van hem over te typen.

## In `combine` varieert het eerste argument het langzaamst

Bij `combine(A, B, ...)` is het EERSTE argument het zwaarste cijfer. Gemeten met drie bij twee:

```
rij 0: a0_b0   rij 2: a1_b0   rij 4: a2_b0
rij 1: a0_b1   rij 3: a1_b1   rij 5: a2_b1
```

Dat is bepalend zodra de rijvolgorde een voorrangsvolgorde is. `Trede_T` kiest met `ArgMin` de laagst genummerde klasse die waar is, dus de as die in de `combine` vooraan staat domineert de hele ladder. In `VariantParameters/Tredes/Wonen.dms` is dat `PlancapaciteitPlusStimuli`, en `IterSubsector_T` maakt de ordening bovendien strikt lexicografisch, zodat een hogere trede altijd voorgaat op elke lagere, ongeacht de geschiktheid.

Wie de volgorde van de argumenten omdraait verandert dus de betekenis van de hele ladder, zonder dat er aan de cardinaliteit of aan de namen iets te zien is.
## Een template kan op vier manieren aangeroepen worden

Zoek je uit of een template nog gebruikt wordt, dan zijn letterlijke treffers niet genoeg. Een template kan rechtstreeks worden aangeroepen, via de stringvorm in `for_each_ne`, via een uit stukken opgebouwde naam (`Dairy_T` en `Akkerbouw_T` komen uit `LandbouwKlasses/Templatetype`), en zonder haakjes als `container X : = Vergridding_T { ... }`. Die laatste twee hebben nul letterlijke treffers en draaien wel degelijk.
