---
name: rs-fingerprints
description: De vaste controle op ontkoppelde bestanden in RSopen; staat de fingerprint van elk weggeschreven bestand nog gelijk aan de invoer die de uitkomst bepaalt. Gebruik dit na elke wijziging in cfg/ die een weggeschreven bestand kan raken, en als afsluiting van een sessie waarin aan het model is gewerkt.
---

# Fingerprints van ontkoppelde bestanden

RSopen maakt een ontkoppeld bestand alleen opnieuw als het er niet is of als de bepalende invoer is veranderd. Naast elk ontkoppeld bestand staat `<bestandsnaam>.params.txt` met de fingerprint: de lijst waarden die de uitkomst bepalen, als `sleutel=waarde` gescheiden door puntkomma's, met Engelse sleutelnamen.

```
bgt_date=20260819;study_area=Nederland;variant=BAU;class_set=Default;class_count=128;class_flags=0000...;grid_size=25
```

Het mechanisme zelf staat beschreven in de Descr van `cfg/main/Templates/DecoupledFile_T.dms` en op de wiki onder Ontkoppelde-bestanden. Lees die als je het patroon moet toepassen. Deze skill gaat over de controle.

## Waarom dit een vaste taak is

Vergeet je een determinant in de fingerprint, dan gebruikt het model stilzwijgend een verouderd bestand. Er komt geen foutmelding, geen waarschuwing en geen afwijkende bestandsnaam. Dat is erger dan altijd opnieuw rekenen, want de uitkomst ziet er normaal uit. Dit is niet met de hand bij te houden naast het gewone ontwikkelwerk, dus het is expliciet aan Claude toebedeeld. Vraag hier niet elke keer toestemming voor: doe de controle en meld alleen wat er moet veranderen.

## De controle

1. Bepaal wat er is gewijzigd sinds de vorige controle. `git log --oneline` en `git diff` tegen de laatst gecontroleerde commit.
2. Voor elke wijziging: kan dit de uitkomst van een weggeschreven bestand veranderen. Kijk niet alleen naar directe invoer maar ook naar wat er doorheen loopt, zoals een klassenindeling, een schakelaar in ModelParameters of een vintage van brondata.
3. Zo ja, staat die invoer in de fingerprint van dat bestand, of anders in de bestandsnaam. Zo nee, meld het en stel de aanvulling voor.
4. Raakt de wijziging een bestand zonder fingerprint, meld dan expliciet dat het bestand met de hand ververst moet worden voordat er weer gerekend wordt. Een ontkoppeld bestand wordt niet herschreven zolang het bestaat, want er is geen automatische invalidatie: verwijder het eerst en draai dan de Write-run.
5. Is er gedraaid met de wijziging, kijk dan ook waar er is geschreven: grep het log op `storage write`. Een item dat op de share schrijft in plaats van onder `%LocalDataProjDir%` is een fout, ook al zegt de exitcode niets. Zie het kopje over schrijf-eenmaal-opslag.

Een fingerprint bevat ALLE bepalende waarden, ook die al in de bestandsnaam zitten. Dat is bewust dubbelop, zodat de regel geen uitzonderingen kent en het zijbestand een volledig verslag is.

## Waar de determinanten zitten die je makkelijk mist

- Schakelaars in `ModelParameters` en `ModelParameters/Advanced` die verderop in de keten doorwerken. Twee gevallen die eerder gemist zijn: `BAG_LogistiekDynamisch` werkt via `IsLogistiekFunctie` door naar de Jobs6-verdeling en de pandfootprint, en de keuze om de verblijfsrecreatiestand alleen binnen de CBS-gebieden te tellen (#364, sinds #801 vast) raakte stand, footprint en de BAG-nieuwbouwdelta. Een schakelaar die vast wordt ingebouwd houdt zijn sleutel in de fingerprint als letterlijke waarde, zodat de bestaande zijbestanden geldig blijven.
- Klassenindelingen. Een wijziging binnen een bestaande set verandert de bestandsnaam niet, dus de set moet zelf in de fingerprint. Daarvoor dient `class_flags`, de nullen-en-enen-reeks van de set.
- Afgeleide kaarten die alleen een bronvintage in hun naam dragen en geen fingerprint hebben. De BGT-capaciteitskaarten voor piekbuiberging (`WriteBaseData/Impl/WaterbergingCapaciteit`, de Make-items in `SourceData/Grondgebruik/bgt.dms`) heten naar `BGT_file_date` en het studiegebied, maar zijn opgebouwd uit de klassenindeling in `Classifications/Grondgebruik/BGT.dms`. Wijzigt die indeling, zoals met de nieuwe klassegroepen van #757, dan leest het model stil de oude kaart terug totdat de kaarten opnieuw zijn weggeschreven. Ontbreken ze, dan geeft de keten per laag een GDAL-fout met exitcode 0 en een leeg aanbod. Meld zo'n kaart als bestand zonder fingerprint; de indeling hoort erin via `class_flags`, net als bij de andere klassenindelingen.
- Vintages van brondata die alleen in een pad of in een itemnaam voorkomen.
- Hardgecodeerde jaartallen in een berekening, zoals het WOZ-jaar 2017 bij de verwervingskosten van niet-woningen.
- De rekenregel zelf. Een reparatie aan de logica verandert de uitkomst zonder dat er een invoer verandert, dus een fingerprint van alleen invoer ziet haar niet. Geef zo'n regel een versiesleutel als parameter naast de code, met het issuenummer van de laatste wijziging als waarde, en verander die mee. De opbrengstdervingskaarten hebben er sinds #837 drie: `lookup` voor de opzoeking in de WWL-relatiedatabase, `gxg_fill` en `soil_fill` voor de vulling van grondwaterstand en BOFEK. De set van 13 september 2026 was met de foute opzoeking gemaakt en bleef na de reparatie zonder enige waarschuwing in gebruik.
- Een invoer die zelf live wordt gerekend en te breed is om als lijst op te nemen, zoals de veenallocatie onder de grondwaterstanden van NbSGenuanceerd. Neem dan een controlesom over de uitkomst op: een som in uint64 over de cellen van de klassewaarde maal een plekgewicht, zodat twee cellen die van klasse wisselen de som veranderen (`SourceData/Water/Grondwaterstanden/NbSGenuanceerd/Oplegging_Herkomst`). Een telling per klasse is niet genoeg: een andere seed voor de bouwsteentrekking hield het aantal veencellen gelijk en verschoof alleen welke bouwsteen waar ligt. Reken in gehele getallen, dan hangt de som niet af van de volgorde waarin threads optellen en geven twee processen hetzelfde getal. De prijs: MayReuse staat in een meta-expressie, dus ook wie de kaart alleen teruggelezen wil zien rekent die keten door, voor de veenallocatie 28 s en 14 GB, en in de GUI kost uitklappen van zo'n item diezelfde tijd.

## Lezers tellen

Of een ontkoppeld bestand zijn schrijftijd waard is, lees je af aan het log van een volledige reeks. Kruis de regels `storage write] Writing to` van de prep-stappen met de regels `storage read] Read ... from` van alle latere processen, allebei gefilterd op het `%LocalDataProjDir%`-pad. De tijd per bestand volgt uit het verschil tussen twee opeenvolgende write-regels; opgeteld komt dat uit op de wandkloktijd van de stap. In een opzet met een proces per zichtjaar bestaat een ontkoppeld bestand met een enkele lezer niet: elk proces leest de basisdata opnieuw, dus de vraag is nooit of iets vaak genoeg gebruikt wordt, maar of het uberhaupt een lezer heeft. Wat geen lezer heeft is een kandidaat om uit de Generate-lijst te halen.

## De registratie

Welke bestanden een fingerprint hebben en met welke sleutels, staat op de wiki-pagina Ontkoppelde-bestanden. Werk die bij als er iets verandert. Twee dingen die daar bewust anders zijn:

- De standbestanden per zichtjaar hebben met opzet geen fingerprint. Die hangen van vrijwel de hele configuratie af, dus een fingerprint zou de hele config moeten omvatten. Ze worden elke run opnieuw geschreven.
- Bestanden op `%RSo_DataDir%` en `%PrivDataDir%` krijgen een vintage plus een versienummer in de naam in plaats van een fingerprint. Zie de regel over schrijf-eenmaal-opslag hieronder.

## Twee GeoDMS-valkuilen en de volgorde van het zijbestand

`ExplicitSuppliers` op een container lift NIET mee wanneer je een los kind opvraagt. Bij for_each-containers kan het schrijven van het zijbestand dus niet aan de container hangen. De nette oplossing is een klein template dat per item de drieslag plus eigen Decoupling maakt; dat staat nog open.

`PropValue(item, 'StorageName')` geeft de expressietekst terug, niet de uitkomst. Dat werkt als je hem weer als StorageName gebruikt, maar niet als invoer voor `ExistingFile`. Zet het pad dan als eigen `parameter<String>` neer en verwijs daar vanuit beide kanten naar.

Het zijbestand hoort onder het bestand te hangen en niet andersom. GeoDMS werkt een leverancier bij voordat het item zelf wordt uitgerekend, en het bestand wordt pas aan het eind van die berekening geschreven. Stond `Write_Fingerprint` als ExplicitSupplier aan het schrijvende item, dan ontstond het zijbestand dus aan het begin van de rekentijd, en liet een run die daarin afbreekt een nieuwe fingerprint naast het oude bestand achter; was de remake nodig omdat de invoer veranderde, dan las de volgende run dat oude bestand als geldig. Gemeten op 2026-09-22 bij #837: beregening van B2 naar B1, de remake afgebroken, en de volgende run met B1 las de B2-kaart met `may_reuse=True`.

Sinds #837 keert `DecoupledFile_T` de volgorde zelf om. Het sjabloon heeft een derde argument `Writers`, de naam of namen van de items die het bestand schrijven, en hangt die als `ExplicitSuppliers` onder `Write_Fingerprint`. De gebruikerskant staat daarom als drieslag neer: `Write_X` draagt de `StorageName`, `Make_X := Write_X` draagt `ExplicitSuppliers = "Decoupling_X/Write_Fingerprint"`, en het kanonieke schakelitem kiest tussen `Calc_X`, `Read_X` en `Make_X`. Vraag altijd `Make_X` en nooit `Write_X`: langs `Write_X` ontstaat er geen zijbestand. Het extra doorgeefitem kost niets, gemeten op een kaart van 196 miljoen cellen: 17,2 s en 836 tegen 835 MB. Een `Writers` die niet oplost valt luid om, exit 1 met `ExplicitSupplier '../...' not found`, en schrijft niets.

Er blijft een venster tussen het bestand en zijn zijbestand, en dat is precies het deel van de fingerprint dat niet al voor het bestand zelf is uitgerekend. Bij de opbrengstdervingskaarten is het nul tot een seconde: de veenallocatie die de fingerprint nodig heeft zit ook onder de grondwaterstanden van de kaart, dus als het zijbestand aan de beurt is staat die er al. Bij de MNP-beheertypenkaart is het dertig seconden op een run van 150, want daar staat de fingerprint naast de kaart en wordt hij apart betaald. Beide gemeten op 2026-09-22 met GeoDms20.17.0.m.

Schrijft een gebruiker meer dan een bestand, een mmd met meer attributen of een hele set, noem ze dan alle in `Writers`, gescheiden door een puntkomma, en noem data-items en nooit de container: een container als leverancier werkt de hele boom eronder bij. Zo staat de basisjaarstand erin met haar 33 schrijvers en de zonneladder met haar treden; hun `Generate` vraagt alleen nog het zijbestand.

## Schrijf-eenmaal-opslag

`%sourceDataDir%`, dus ook `%RSo_DataDir%` en `%PrivDataDir%`, synchroniseert met Nextcloud. Daar mag een bestand wel geplaatst maar niet gewijzigd of verwijderd worden. Een item dat naar zo'n pad schrijft en al een bestand aantreft krijgt geen foutmelding: Nextcloud zet er een conflicted copy naast, met de nieuwe inhoud onder de conflicted naam en de oude onder de originele, of laat een `.<naam>.~<hex>`-restant achter, en de run eindigt met exitcode 0. Opruimen kan alleen de beheerder en dat duurt weken. Daaruit volgen drie regels.

Wat legitiem naar de brondata schrijft, schrijft eenmaal. Zulke items heten `Write_*` of `Make*`, hebben een read-only zusteritem ernaast dat het bestand terugleest, en vuren alleen als je er expliciet om vraagt. Het bestand krijgt de vintage en een versienummer in de naam, en die versie gaat omhoog bij elke inhoudelijke wijziging aan de regel of de drempels. Zet het volledige pad als parameter in ModelParameters, zodat schrijf- en leeskant gegarandeerd dezelfde naam gebruiken.

Modeluitvoer, test-exports en ontkoppelde tussenbestanden horen onder `%LocalDataProjDir%`, met de conventie `%LocalDataProjDir%/BaseData/<domein>/<bron>/<naam>_<StudyArea>.tif`. De studiegebied-suffix is nodig omdat AdminDomain met het studiegebied meebeweegt: zonder suffix leest een run op een deelgebied het Nederland-bestand in een kleiner domein, wat een FileTileArray-fout met exitcode 0 en een leeg resultaat geeft. Let bij de controle op items met een expressie en een StorageName maar zonder leeskant: die schrijven bij elke run waarin ze worden aangeraakt, en staat die StorageName op de share, dan overschrijft elke run stil de vorige. Zo herschreef de opbrengstdervingsketen in `SourceData/Landbouw.dms` een tijdlang haar kaarten naar `%RS_Lb_DataDir%` bij elke landbouwgeschiktheid; het pad staat sindsdien onder `%LocalDataProjDir%` en het item heeft een Read-zuster.

Toets na een run met een wijziging waar er is geschreven, met een grep op `storage write` in het log. De exitcode zegt hier niets. Wat er gebeurt als een bronbestand op de share hernoemd of verplaatst is, en hoe je dat aan het log herkent, staat in de skill geodms-valkuilen.
