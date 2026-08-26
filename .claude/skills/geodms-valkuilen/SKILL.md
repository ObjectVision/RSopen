---
name: geodms-valkuilen
description: Stille fouten in GeoDMS-configuratie die geen foutmelding geven maar wel een verkeerd antwoord; naamafscherming en de kale name, poly2grid-volgorde bij geneste polygonen, PropValue op StorageName, ExplicitSuppliers op een container, null-semantiek en off-grid rasters. Lees dit voordat je DMS-code in RSopen schrijft of wijzigt.
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

## PropValue geeft de expressietekst

`PropValue(item, 'StorageName')` geeft de expressietekst terug, niet de uitkomst. Dat werkt als je hem meteen weer als StorageName gebruikt, maar niet als invoer voor iets dat een echt pad verwacht, zoals `ExistingFile`. Zet het pad dan als eigen `parameter<String>` neer en verwijs daar vanuit beide kanten naar.

## Null-semantiek

`null < x` en `0f/0f < x` geven FALSE. Er is dus geen null-propagatie naar bool, ook niet door `&&` of `OR(...)` heen. Een null-conditie in een `switch` valt door naar de default.

Dat is handig zolang je het weet en een valkuil zodra je aanneemt dat een null zich door een vergelijking heen plant.

## Rasters die niet op het modelraster liggen

GeoDMS leest een raster op georeferentie, niet positioneel, en rondt een niet-gehele celoffset af naar de dichtstbijzijnde cel. Dat gaat goed zolang alle lagen dezelfde afronding krijgen, maar het levert een GridStorageManager-waarschuwing op en het is niet zichtbaar in de uitkomst.

Het recept in RSopen is een `Bron`-container die het originele bestand leest en een `Maak`-container die het als tif op het modelraster wegschrijft, waarna de gewone laagnamen de tif read-only lezen. Toegepast op ABCD, bodemdaling en risicozonering. Bijvangst: 394 MB ASCII werd 3,6 MB tif en de inleestijd ging van 22,5 naar 0,5 s.

Let op dat GeoDMS geen NODATA-tag schrijft. Binnen GeoDMS is de nullwaarde null, maar QGIS en Python tonen hem als gewone waarde. Zet die tag zelf als het bestand buiten GeoDMS gebruikt wordt.

## Er is geen CalcCache meer

De CalcCache, de persistente schijfcache met automatische invalidatie, is verdwenen sinds de GeoDMS 8-serie. Presenteer hem nooit als bestaande voorziening; wiki-pagina's die er in de tegenwoordige tijd over schrijven zijn GeoDMS 7-documentatie.

De huidige praktijk is strategisch ontkoppelen: stabiele tussenresultaten expliciet wegschrijven naar in de configuratie gedeclareerde storages en in een latere run teruglezen. Er is geen automatische invalidatie; het verversen na een wijziging bovenstrooms is een bewuste stap. Zie de skill rs-fingerprints.

## Een template kan op vier manieren aangeroepen worden

Zoek je uit of een template nog gebruikt wordt, dan zijn letterlijke treffers niet genoeg. Een template kan rechtstreeks worden aangeroepen, via de stringvorm in `for_each_ne`, via een uit stukken opgebouwde naam (`Dairy_T` en `Akkerbouw_T` komen uit `LandbouwKlasses/Templatetype`), en zonder haakjes als `container X : = Vergridding_T { ... }`. Die laatste twee hebben nul letterlijke treffers en draaien wel degelijk.
