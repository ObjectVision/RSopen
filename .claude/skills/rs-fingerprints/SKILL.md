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

- Schakelaars in `ModelParameters` en `ModelParameters/Advanced` die verderop in de keten doorwerken. Twee gevallen die eerder gemist zijn: `BAG_LogistiekDynamisch` werkt via `IsLogistiekFunctie` door naar de Jobs6-verdeling en de pandfootprint, en `Verblijfsrecreatie/StandAlleenInCBSGebied` raakt stand, footprint en de BAG-nieuwbouwdelta.
- Klassenindelingen. Een wijziging binnen een bestaande set verandert de bestandsnaam niet, dus de set moet zelf in de fingerprint. Daarvoor dient `class_flags`, de nullen-en-enen-reeks van de set.
- Afgeleide kaarten die alleen een bronvintage in hun naam dragen en geen fingerprint hebben. De BGT-capaciteitskaarten voor piekbuiberging (`WriteBaseData/Impl/WaterbergingCapaciteit`, de Make-items in `SourceData/Grondgebruik/bgt.dms`) heten naar `BGT_file_date` en het studiegebied, maar zijn opgebouwd uit de klassenindeling in `Classifications/Grondgebruik/BGT.dms`. Wijzigt die indeling, zoals met de nieuwe klassegroepen van #757, dan leest het model stil de oude kaart terug totdat de kaarten opnieuw zijn weggeschreven. Ontbreken ze, dan geeft de keten per laag een GDAL-fout met exitcode 0 en een leeg aanbod. Meld zo'n kaart als bestand zonder fingerprint; de indeling hoort erin via `class_flags`, net als bij de andere klassenindelingen.
- Vintages van brondata die alleen in een pad of in een itemnaam voorkomen.
- Hardgecodeerde jaartallen in een berekening, zoals het WOZ-jaar 2017 bij de verwervingskosten van niet-woningen.

## Lezers tellen

Of een ontkoppeld bestand zijn schrijftijd waard is, lees je af aan het log van een volledige reeks. Kruis de regels `storage write] Writing to` van de prep-stappen met de regels `storage read] Read ... from` van alle latere processen, allebei gefilterd op het `%LocalDataProjDir%`-pad. De tijd per bestand volgt uit het verschil tussen twee opeenvolgende write-regels; opgeteld komt dat uit op de wandkloktijd van de stap. In een opzet met een proces per zichtjaar bestaat een ontkoppeld bestand met een enkele lezer niet: elk proces leest de basisdata opnieuw, dus de vraag is nooit of iets vaak genoeg gebruikt wordt, maar of het uberhaupt een lezer heeft. Wat geen lezer heeft is een kandidaat om uit de Generate-lijst te halen.

## De registratie

Welke bestanden een fingerprint hebben en met welke sleutels, staat op de wiki-pagina Ontkoppelde-bestanden. Werk die bij als er iets verandert. Twee dingen die daar bewust anders zijn:

- De standbestanden per zichtjaar hebben met opzet geen fingerprint. Die hangen van vrijwel de hele configuratie af, dus een fingerprint zou de hele config moeten omvatten. Ze worden elke run opnieuw geschreven.
- Bestanden op `%RSo_DataDir%` en `%PrivDataDir%` krijgen een vintage plus een versienummer in de naam in plaats van een fingerprint. Zie de regel over schrijf-eenmaal-opslag hieronder.

## Twee GeoDMS-valkuilen die hierbij horen

`ExplicitSuppliers` op een container lift NIET mee wanneer je een los kind opvraagt. Bij for_each-containers kan het schrijven van het zijbestand dus niet aan de container hangen. De nette oplossing is een klein template dat per item de drieslag plus eigen Decoupling maakt; dat staat nog open.

`PropValue(item, 'StorageName')` geeft de expressietekst terug, niet de uitkomst. Dat werkt als je hem weer als StorageName gebruikt, maar niet als invoer voor `ExistingFile`. Zet het pad dan als eigen `parameter<String>` neer en verwijs daar vanuit beide kanten naar.

## Schrijf-eenmaal-opslag

`%sourceDataDir%`, dus ook `%RSo_DataDir%` en `%PrivDataDir%`, synchroniseert met Nextcloud. Daar mag een bestand wel geplaatst maar niet gewijzigd of verwijderd worden. Een item dat naar zo'n pad schrijft en al een bestand aantreft krijgt geen foutmelding: Nextcloud zet er een conflicted copy naast, met de nieuwe inhoud onder de conflicted naam en de oude onder de originele, of laat een `.<naam>.~<hex>`-restant achter, en de run eindigt met exitcode 0. Opruimen kan alleen de beheerder en dat duurt weken. Daaruit volgen drie regels.

Wat legitiem naar de brondata schrijft, schrijft eenmaal. Zulke items heten `Write_*` of `Make*`, hebben een read-only zusteritem ernaast dat het bestand terugleest, en vuren alleen als je er expliciet om vraagt. Het bestand krijgt de vintage en een versienummer in de naam, en die versie gaat omhoog bij elke inhoudelijke wijziging aan de regel of de drempels. Zet het volledige pad als parameter in ModelParameters, zodat schrijf- en leeskant gegarandeerd dezelfde naam gebruiken.

Modeluitvoer, test-exports en ontkoppelde tussenbestanden horen onder `%LocalDataProjDir%`, met de conventie `%LocalDataProjDir%/BaseData/<domein>/<bron>/<naam>_<StudyArea>.tif`. De studiegebied-suffix is nodig omdat AdminDomain met het studiegebied meebeweegt: zonder suffix leest een run op een deelgebied het Nederland-bestand in een kleiner domein, wat een FileTileArray-fout met exitcode 0 en een leeg resultaat geeft. Let bij de controle op items met een expressie en een StorageName maar zonder leeskant: die schrijven bij elke run waarin ze worden aangeraakt, en staat die StorageName op de share, dan overschrijft elke run stil de vorige. Zo herschreef de opbrengstdervingsketen in `SourceData/Landbouw.dms` een tijdlang haar kaarten naar `%RS_Lb_DataDir%` bij elke landbouwgeschiktheid; het pad staat sindsdien onder `%LocalDataProjDir%` en het item heeft een Read-zuster.

Toets na een run met een wijziging waar er is geschreven, met een grep op `storage write` in het log. De exitcode zegt hier niets. Wat er gebeurt als een bronbestand op de share hernoemd of verplaatst is, en hoe je dat aan het log herkent, staat in de skill geodms-valkuilen.
