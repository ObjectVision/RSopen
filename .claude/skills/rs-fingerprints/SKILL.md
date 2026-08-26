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
4. Raakt de wijziging een bestand zonder fingerprint, meld dan expliciet dat het bestand met de hand ververst moet worden voordat er weer gerekend wordt.

Een fingerprint bevat ALLE bepalende waarden, ook die al in de bestandsnaam zitten. Dat is bewust dubbelop, zodat de regel geen uitzonderingen kent en het zijbestand een volledig verslag is.

## Waar de determinanten zitten die je makkelijk mist

- Schakelaars in `ModelParameters` en `ModelParameters/Advanced` die verderop in de keten doorwerken. Twee gevallen die eerder gemist zijn: `BAG_LogistiekDynamisch` werkt via `IsLogistiekFunctie` door naar de Jobs6-verdeling en de pandfootprint, en `Verblijfsrecreatie/StandAlleenInCBSGebied` raakt stand, footprint en de BAG-nieuwbouwdelta.
- Klassenindelingen. Een wijziging binnen een bestaande set verandert de bestandsnaam niet, dus de set moet zelf in de fingerprint. Daarvoor dient `class_flags`, de nullen-en-enen-reeks van de set.
- Vintages van brondata die alleen in een pad of in een itemnaam voorkomen.
- Hardgecodeerde jaartallen in een berekening, zoals het WOZ-jaar 2017 bij de verwervingskosten van niet-woningen.

## De registratie

Welke bestanden een fingerprint hebben en met welke sleutels, staat op de wiki-pagina Ontkoppelde-bestanden. Werk die bij als er iets verandert. Twee dingen die daar bewust anders zijn:

- De standbestanden per zichtjaar hebben met opzet geen fingerprint. Die hangen van vrijwel de hele configuratie af, dus een fingerprint zou de hele config moeten omvatten. Ze worden elke run opnieuw geschreven.
- Bestanden op `%RSo_DataDir%` en `%PrivDataDir%` krijgen een vintage plus een versienummer in de naam in plaats van een fingerprint. Zie de regel over schrijf-eenmaal-opslag hieronder.

## Twee GeoDMS-valkuilen die hierbij horen

`ExplicitSuppliers` op een container lift NIET mee wanneer je een los kind opvraagt. Bij for_each-containers kan het schrijven van het zijbestand dus niet aan de container hangen. De nette oplossing is een klein template dat per item de drieslag plus eigen Decoupling maakt; dat staat nog open.

`PropValue(item, 'StorageName')` geeft de expressietekst terug, niet de uitkomst. Dat werkt als je hem weer als StorageName gebruikt, maar niet als invoer voor `ExistingFile`. Zet het pad dan als eigen `parameter<String>` neer en verwijs daar vanuit beide kanten naar.

## Schrijf-eenmaal-opslag

`E:\SourceData`, dus ook `%RSo_DataDir%` en `%PrivDataDir%`, synchroniseert met Nextcloud. Een eenmaal geplaatst bestand mag daar niet gewijzigd of verwijderd worden. Overschrijven levert een conflicted copy op waarbij de nieuwe inhoud in de conflicted naam belandt en de oude onder de originele naam blijft staan. Opruimen kan alleen de beheerder en dat duurt weken.

Elk bestand dat het model daarheen schrijft krijgt de vintage en een versienummer in de naam, en die versie gaat omhoog bij elke inhoudelijke wijziging aan de regel of de drempels. Zet het volledige pad als parameter in ModelParameters, zodat schrijf- en leeskant gegarandeerd dezelfde naam gebruiken. Test-exports en tussenproducten horen in `%LocalDataProjDir%`, niet op de share.
