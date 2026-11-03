# Briefing voor auditrollen

Elke rol in `.claude/agents/` leest dit bestand als eerste. Hier staat wat het model is,
hoe je erin zoekt, welke bewijsregel geldt en hoe je rapporteert.

## Het model

RSOpen is de open source versie van RuimteScanner, een rasterallocatiemodel voor Nederland,
ontwikkeld door PBL samen met Object Vision, de VU en Deltares. De configuratie is geschreven
in GeoDMS, in bestanden met de extensie `.dms`.

De keten is grofweg: claims per sector, subsector en allocatieregio, geschiktheid per cel,
een zeef die bepaalt waar iets mag landen, de allocatie zelf per sector en allocatieregio, en
daarna de indicatoren die over de resulterende stand rekenen.

Er zijn varianten, bijvoorbeeld BAU, NbSMax en NbSGenuanceerd, en zichtjaren, bijvoorbeeld
2030 en 2040. De stand aan het eind van een zichtjaar is het startpunt van het volgende, dus
er is padafhankelijkheid. Een fout in 2030 zit ook in 2040.

## De wiki is het naslagwerk

De wiki bij deze repo beschrijft de methoden, de aannames en de ontwerpkeuzen van het model. Daar
staat de bedoeling. Lees de pagina's die bij jouw vak horen voordat je een oordeel velt over een
rekenregel.

De wiki is een eigen git-repository naast deze repo. Je leest hem op
https://github.com/ObjectVision/RSopen/wiki, of je haalt hem binnen met
`git clone https://github.com/ObjectVision/RSopen.wiki.git` en grept er daarna doorheen.

Gebruik de wiki als toetssteen. Zegt de wiki iets anders dan de configuratie doet, dan is dat
altijd een bevinding: of de configuratie klopt niet, of de documentatie is achtergebleven bij een
wijziging. Zeg erbij welke van de twee je denkt dat het is, en waarom.

## Eigenaardigheden van de configuratie die je moet kennen

GeoDMS is declaratief. Een item wordt pas gerekend als er iets om vraagt. Veel configuratie
wordt gegenereerd met `for_each`-varianten en met strings die naar itempaden verwijzen. Twee
gevolgen die telkens terugkomen als echte fout:

Een verwijzing naar een item dat niet bestaat valt niet op zolang niemand hem trekt. Dode
verwijzingen in `ExplicitSuppliers` of in een gegenereerde string zijn dus een reëel type
bevinding. Controleer of het pad waarnaar verwezen wordt echt bestaat.

Een item met een `StorageName` wordt alleen weggeschreven als er iets is dat hem trekt,
meestal een `Generate`-parameter met `ExplicitSuppliers`. Staat het item niet in die lijst,
dan blijft er een oud bestand op schijf staan met de oude betekenis. Kijk dus niet alleen of
de rekenregel klopt, maar ook of het resultaat daadwerkelijk wordt geproduceerd.

Eenheden zijn expliciet, bijvoorbeeld `[Ha]`, `[Woning]`, `[meter2]`, `[Job]`. Eenheidsfouten
zijn een terugkerende bron van bugs. Reken bij twijfel een regel na.

`Descr` bevat de bedoeling van een item en `IntegrityCheck` bevat een harde eis. Als de tekst
in `Descr` iets anders zegt dan de formule doet, is dat een bevinding.

## Zoeken, niet aannemen

Deze repo is de open versie. Projectconfiguraties, zoals die voor NL2120, hebben deels andere
paden en extra bestanden. Ga daarom nooit uit van een pad uit deze briefing of uit een issue,
maar zoek het bestand op naam of op inhoud met grep en glob, en meld welk pad je werkelijk
hebt gebruikt.

## Wat je wel en niet kunt

Het model zelf draait alleen met GeoDMS op de machine van de gebruiker. In een sessie op
afstand kun je de configuratie lezen en de issues in deze repo, en verder niets rekenen.
Lokaal kun je daarnaast uitdraaien lezen, bijvoorbeeld csv-exports en GeoTIFF-bestanden.

Je wijzigt de configuratie niet. Je leest, je meet en je rapporteert. Een reparatievoorstel
mag je opschrijven, maar je voert hem niet uit.

## Skills in deze repo

Staat er een map `.claude/skills`, gebruik dan wat daarin staat en herhaal het niet. Waar een skill
iets anders zegt dan deze briefing, gaat de skill voor, want die hoort bij de projectconfiguratie.

`geodms-valkuilen` geeft de volledige lijst stille fouten in GeoDMS, ruimer dan de vier hierboven.
Lees hem voordat je een oordeel velt over een rekenregel.

`rs-toetsen` beschrijft hoe een uitkomst inhoudelijk wordt getoetst, in drie lagen: interne
consistentie, orde van grootte tegen referentiewaarden, en ruimtelijke patronen. Houd die volgorde
aan. Een patroon analyseren terwijl een randtotaal niet sluit is verspilde moeite.

`rs-draaien` zegt wat een controle kost en hoe je hem zo goedkoop mogelijk houdt.

`rs-fingerprints` beantwoordt de vraag of een weggeschreven bestand werkelijk opnieuw is gemaakt.
Gebruik hem zodra je vermoedt dat een resultaat van vóór een wijziging stamt.

`rs-issues` regelt tekst die op GitHub terechtkomt.

## De bewijsregel

Elke bevinding heeft een vindplaats: een bestand met regelnummer, of een indicator met een
getal en de eenheid erbij. Zonder vindplaats geen bevinding. Vermoedens mogen, maar dan in de
aparte lijst onderaan, met wat je nodig zou hebben om ze na te gaan.

Gebruik alleen getallen die je zelf hebt gelezen of gemeten, en zet de bron erbij. Neem geen
getal over uit je geheugen of uit een eerdere ronde zonder het opnieuw te controleren.

Onderscheid drie soorten bevindingen. Een fout in de configuratie, dus iets dat aantoonbaar
anders werkt dan bedoeld. Een keuze die opnieuw genomen moet worden, dus iets dat werkt zoals
geconfigureerd maar waarvan de aanname niet meer houdbaar is. En ontbrekende onderbouwing, dus
iets waarvan de bron of de aanname niet te vinden is.

Oordeel niet over codestijl of opmaak. Het gaat om de inhoud van jouw vakgebied.

## Rapportvorm

Lever precies deze structuur, zwaarste bevinding eerst.

```
## Rol en scope
Wat je hebt bekeken, en in welke bestanden.

## Bevindingen

### 1. Korte titel
Vindplaats: bestand en regel, of indicator en getal
Wat er staat: feitelijk, zonder interpretatie
Waarom dit volgens mijn vak niet klopt: de vakinhoudelijke redenering
Gevolg voor de uitkomst: wat er misgaat in de resultaten, zo mogelijk met orde van grootte
Soort: fout, keuze opnieuw nemen, of ontbrekende onderbouwing
Zwaarte: hoog, midden of laag, met een reden
Zekerheid: geverifieerd of vermoeden

## Gecontroleerd en in orde
Wat je hebt getoetst en wat klopte. Dit is even belangrijk als de bevindingen.

## Niet kunnen nagaan
Wat buiten bereik bleef en wat je ervoor nodig hebt.
```

## Je plaatst zelf niets

Je rapport is een concept. Je plaatst geen issue, geen comment en geen reactie op GitHub, ook niet
als je bevinding hard is. Iemand anders leest hem en beslist wat ermee gebeurt. De repo is openbaar
en elke comment bereikt direct alle betrokkenen bij PBL, Deltares en de VU.

## Schrijfregels

De issues in deze repo zijn openbaar. Noem geen namen van personen, verwijs naar de
organisatie: PBL, Object Vision, VU, Deltares. Gebruik vet alleen voor kopjes en niet in de
lopende tekst. Gebruik geen gedachtenstreepjes, herschrijf de zin of gebruik een komma, een
dubbele punt of een punt. Schrijf in het Nederlands.
