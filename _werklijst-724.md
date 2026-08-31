# Werklijst toetsing #724

Vierentwintig wijzigingen tussen commit f9c8d172 (30 augustus, tag `oplevering_NL2120_20260830`, de codestand van de productieruns) en de avond van 31 augustus. Per wijziging het oordeel en waarop dat rust.

Oordelen: **geslaagd** is gemeten en het getal klopt met wat de wijziging beloofde. **gezakt** is gemeten en het klopt niet. **zwak** is wel een getal maar zonder referentie om het tegen af te zetten. **deels** is een van de twee helften getoetst. **open** is niet gemeten.

Gemeten op codestand 338bde9c tot en met 2b581dae, met de standen van Y2040 die op 31 augustus opnieuw zijn doorgerekend voor BAU (47,1 min) en NbSGenuanceerd (50,0 min). Waar een getal van een ander dan mijzelf komt staat dat erbij.

Let op de vintage binnen deze lijst zelf, want dit is precies het patroon dat hij beschrijft. Ronde 3 startte om 20:11 op 0bd7de6d en er is tijdens die ronde in de configuratie geschreven: `2b581dae` (#725, SOMERS_CO2_T.dms) om 20:24:56 en een include van een nieuw `Diagnose620.dms` in `main.dms` om 20:31. Geen van de twintig items van ronde 3 leest SOMERS en de include is additief, dus de getallen hieronder zijn onderling vergelijkbaar. Wat wel vervalt is `somers_mediaan` uit de diagnoseronde van 18:24 en 19:36; dat getal staat op de code van voor #725 en is niet als geldig opgenomen.

## Rekenpad en meetinstrumenten

Deze vier gaan niet over een issue maar over het vermogen om iets te toetsen. Ze staan vooraan omdat ze de rest blokkeerden.

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 1 | #721 legendabewaking, schrijfkant | gezakt, gerepareerd in fe317807 | `WriteStand/Legenda` stond niet in de ExplicitSuppliers van `Impl/Generate`, dus het zijbestand werd nooit geschreven terwijl de leeskant een stand zonder kloppend zijbestand hard weigert. Gemeten: nul `.params.txt` over twintig standmappen, en `Impl/Stand/OP_rel` gaf exit 1 op `'LegendaKlopt' is not true`. Daarmee lag de hele ontkoppelde indicatorenkant stil en zou een reeks bij het tweede zichtjaar breken. Na de fix staat het zijbestand er voor beide varianten en geeft de leestoets exit 0 |
| 2 | #721 en #723 hernoeming van de 26 NbS-pakketten | open | De `Opbrengsten_perOP`-tifs dragen de oude namen, dus 26 van de 53 zijn per set onvindbaar voor NbSMax en NbSGenuanceerd. Die set heeft geen fingerprint, dus niets signaleert het. De basisjaarzeef loopt er wel doorheen (`Diagnose683` op NbSGenuanceerd in 109 s); of de zichtjaargeschiktheid struikelt is niet aangetoond |
| 3 | #684 meetharnas `Diagnose684` | gezakt als meetinstrument | Het harnas leest `Sloop/Verschil/OpSlotMaarGeenNatuur` onder kolomnamen als `won_zonder_nieuw_lu`, terwijl commit 17f940fa dat item van betekenis heeft veranderd. De uitdraai geeft 29.516 woningen en leest als bewijs dat #684 niets deed. Rechtstreeks gemeten is het 1.436,67 woningen op 10.566,63 ha. Sessie 8f heeft de kolomnamen inmiddels hernoemd in 59998b98 |
| 4 | `/Diagnose/GenerateAll` dekt de losse parameters niet | gezakt als meetinstrument | De ExplicitSuppliers zijn `AsList('Resultaten/'+Checks/name+'/Waarde')`, dus alleen de tabel `Checks`. `grondbalans_bestemmingen`, `claimtoets_werken`, `waterberging_perregio` en de `Samenvatting`-items vallen erbuiten, schrijven naar dezelfde map en dragen geen tijdstempel. Twee keer bijna misgegaan: een bestand van 16:13 gaf 437,5 ha waar de verse 0 geeft, en `waterberging_perregio` van 16:15 toonde juist de BAU-opgave die #664 heeft afgeschaft |

## Sloop, oplegging en de veenlevering

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 5 | #684 sloop vereist een nieuw landgebruik | geslaagd | `Woningen_GeleegdZonderNieuwLandgebruik` 1.436,67 op 10.566,63 ha, precies het rivierensloopgebied, en `Woningen_GespaardDoorKoppeling` 28.079,76 op 94.604,56 ha. Rechtstreeks met `@statistics` gemeten na de commits van #660 en #664, dus vers |
| 6 | #684 uitzondering voor rivieren | geslaagd, met een randgeval | De uitzondering snijdt op het sloopgebied van rivieren uit #620. Op de overlap met veen wint rivieren, dus 12,88 ha veensloopgebied wordt wel geleegd. De zin dat het veendeel nul is klopt in woningen en niet in oppervlak. Onafhankelijk bevestigd door sessie 8f, die op hetzelfde verschil uitkwam |
| 7 | #684 pandentoetsreparatie | doel niet gehaald | `SloopgebiedKrijgtDeNatuur` staat op FALSE, dus `IsSloopgebied` is overal onwaar en de zesde ingang van `NatuurAlloc_T` krijgt overal een leeg masker. In de geleverde stand is dit code die niets doet. De pandentoets bepaalt daarmee feitelijk waar in het veen gesloopt wordt |
| 8 | #660 eindtoestand en overloop | geslaagd in constructie, omvang deels gemeten | Trap 1 in NbSGenuanceerd: claim 258.747,5 ha, gerealiseerd 244.495,81, tekort 14.251,69, verlies door de pandentoets 18.714,50, aaneengeslotenheid 0,8995 tegen 0,5506 aselect. Het eerder genoteerde tekort van 5.096 ha hoort bij een claim van 213.663 ha en is achterhaald door #664. Het restant na trap 2 is niet gemeten |
| 9 | #664 claim nul in de referentievarianten | geslaagd | Op een verse allocatie: `claimreal_Waterberging` komt voor BAU leeg terug, dus geen enkele regio heeft nog een opgave, en `wbcellen_ha` is 0. In NbSGenuanceerd 0,9994 tot 1,0000 over vijf regio's, met 2.872,2 ha waterberging op veen |
| 10 | #664 9a/9b-water als voorkeurslocatie | open | De voorkeursterm `IsVeenAllocWater` maal `Weight_VeenWater_Waterberging` is gebouwd en `ExogeenWaterOpleggen` staat correct uit, maar of de gealloceerde berging werkelijk in de 9a-vlakken valt is niet gemeten. Daarvoor bestaat geen kruising |
| 10b | `ExogeenWaterOpleggen` staat op FALSE, veendeel | bewuste keuze, gevolg vastgelegd | Nagekeken: `VariantK.dms:241` geeft vier keer FALSE, en `Natuur.dms:671` legt uit waarom, namelijk dat de cel zijn water via de sector Waterberging krijgt en dat beide aanzetten de dubbeltelling terugbrengt. Het gevolg voor de sloopregel staat ook opgeschreven, in de Descr van `DoorBouwregime` op `VariantData_T.dms:372`. Ik had dat eerst als ongedocumenteerd genoteerd en dat was onjuist |
| 10d | dezelfde schakelaar, rivierendeel | gezakt | Voor het veen is er een tweede route, want de sector Waterberging alloceert daar. Voor de rivieren niet: het zomerbed, stromend en stagnant water uit die levering zit in geen enkele claim van die sector, dus die hectares komen nergens op de landgebruikskaart terecht en zetten de cel ook niet op slot. `Natuur.dms:1634` benoemt het zelf: "Let op dat ExogeenOpleggen/Totaal in VariantData op dit moment alleen de natuurstroom neemt en de waterstroom laat liggen", en `Zeef_T.dms:53` herhaalt het aan de zeefkant. Omvang, gemeten door een parallelle sessie op codestand 53d44232 met sleutel `opp_bron_riv`: van de 36.131,6 ha nieuw water in NbSGenuanceerd komt 32.961,9 ha uit de veenlevering en 3.169,8 ha uit de rivieren. Alleen dat laatste deel is een gat, en ook daarvan telt alleen het nieuwe water: de rivierenlevering wijst 21.013 ha als water aan, maar 17.843 ha daarvan is bestaand zomerbed en bestaande geulen die al als water te boek staan, dus daar verandert de oplegging niets aan. Op woningen: op het nieuwe veenwater staan 84 woningen die geen van alle wijken, op het nieuwe rivierenwater 331 waarvan er 119 wijken. Een eerdere opgave van 21.013 ha voor dit gat was te hoog en is hier gecorrigeerd. Dat het op twee plekken als openstaand is opgeschreven maakt het geen kleiner probleem, alleen een bekend probleem |
| 10c | koolstofklasse van een gealloceerde waterbergingscel | gezakt, hoort bij #657 | `CarbonStorageSequestration_T.dms:207` bepaalt de klasse als `IsStedelijk ? Dichtbebouwd : MakeDefined(CC_Exogeen, vorige klasse)`, en `CC_Exogeen` op regel 198 is `ExogeenOpleggen/carbonclass_rel`, dus alleen de natuurstroom. Een gealloceerde waterbergingscel is niet stedelijk en krijgt geen exogene oplegging, dus hij houdt zijn oude koolstofklasse terwijl er water ligt. Aangedragen door een parallelle sessie en door mij in de code bevestigd. Dit is het punt dat de eerste doorlichting van #657 als open achterliet en dat er nog steeds staat; het maakt het methaancijfer voor NbSGenuanceerd een ondergrens |

## Zeef en plancapaciteit

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 11 | #683 plan gaat voor op het landschapsregime | geslaagd op de plankant | Basisjaarzeef NbSGenuanceerd: masker 635.990,1 ha, vrijgekomen wonen 2.444,9 ha (1.333,6 hard en 1.111,4 zacht), waarvan 1.356,9 ha de zichtjaarzeef overleeft; nijverheid 35,3 ha. In BAU alle maskermaten nul, maar dat is geen nulmeting van de schakelaars want daar is geen masker |
| 12 | #683 tegenover de schaal van het issue | doel niet gehaald | De opbrengst is 0,38 procent van het masker, terwijl juist het schaalverschil tussen masker en verstedelijking de aanleiding van het issue was. De kruistabel is sinds #660 bovendien verschoven: masker zonder oplegging van 287.557 naar 270.919 ha |

## Ontwikkelpakketten en bouwkosten

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 13 | #721 OP-sets per variant | geslaagd | Gemeten setgroottes 27, 27, 41 en 39, dus 27 plus 14 en 27 plus 12 zoals bedoeld |
| 14 | #721 verschoven dichtheidsvloer | bijwerking, niet vastgelegd | Nagerekend uit de pakkettentabel met vormfactor 0,76 en 0,78. Van de vier WP2xVSSH-combinaties verschuift er precies een: eengezins sociale huur gaat in BAU en BAU2 van 8,22 naar 22,22 woningen per hectare, factor 2,70. Omdat elk default-pakket daar minstens 22,22 haalt, sloot de oude vloer in de leegste gebieden alle pakketten uit en past nu het minst dichte er precies in. Staat in geen issue, commit message of toelichting |
| 15 | #722 BrutoBuurt uitgefaseerd | geslaagd | Verwijdering compleet, per constructie geen uitkomstverandering |
| 16 | #723 bouwwijzemasker met locatiekeuze | geslaagd als equivalentiestap | Alle 27 default-pakketten dragen precies een toegestane bouwwijze, `GeenMaatregelen`. De keuzeregel sluit exact op het celtotaal: drijvend 560.357 plus 55.586.459 en stedelijk 19.261.146 plus 36.885.670, beide 56.146.816. De verruiming van de maskers, de eigenlijke inhoudelijke stap, staat nog open |
| 17 | #673 woningtype-as in de bouwkosten | geslaagd aan de rekenkant | Zes typefactoren gemeten en het mixgewogen gemiddelde per huursector komt op 1,000000 uit. Of de as de keuze tussen ontwikkelpakketten werkelijk verzet is niet gemeten; de ArgMax loopt binnen `OP_subdomain`, dus binnen meergezins kan een WP4-as per constructie niets verzetten |

## Regio-indeling en indicatoren

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 18 | #705 landsdekkende landschapsregio | geslaagd | Kust 434.322,4 ha, rivieren 444.794,9, veen 628.923,7, zand 1.458.118,4, overig 558.997,2, met 3.907,9 ha groot water leeg en 0 ha land zonder regio binnen NL. De overdrachtstabel sluit; de volgorde legt 67.030 ha veenlevering bij rivieren en 224.861 ha zandbegrenzing bij veen |
| 19 | #705 blokindeling van poly2grid naar modus | geslaagd, met een kleine structurele rest die ouder is dan de wijziging | De omzetting is een stille gedragswijziging in de piekbui-indicator die verder niets met #705 te maken heeft en waarvoor geen voor-en-na was gedraaid. De toets is de som van `PerRegio/Vraag` tegen het landelijke totaal. Op de Landschap-indeling, met vijf regio's en lege regio's op groot water: 497.021.127 tegen 497.023.059 m3, dus 1.932 m3 verschil op 497 miljoen. De keuze van indeling introduceert de rest niet: op de indeling NL is het verschil met 2.611 m3 zelfs iets groter dan op Landschap. Wat de rest wel is, is echte weggevallen vraag en geen afrondingsruis, en dat is inmiddels op beide indelingen rechtstreeks gemeten: 1.930,08 m3 vraag in blokken zonder regio tegen een sommenverschil van 1.931,95 op Landschap, en 2.626 tegen 2.611 op NL. Beide paren vallen op enkele kuub samen. Van de 364.000 blokken hebben er 220.333 geen regio, maar dat is vrijwel allemaal zee en buitenland zonder vraag; het mechanisme zijn kust- en grensblokken die deels buiten het regiogebied liggen en toch bebouwd gebied met vraag bevatten. Vier op de miljoen van de landelijke vraag. Gemeten door een parallelle sessie op een losse kopie, met de items `wb_vraag_zonder_regio` en `wb_blokken_zonder_regio`, na twee zelfcorrecties. Niet gemeten, en dit is de enige echt open vraag die overblijft: of de oude poly2grid-blokindeling dezelfde blokken liet vallen. Beide metingen hierboven draaien op de modus-code, dus ze zeggen niets over de vorige versie. Ik heb eerder geschreven dat de rest ouder is dan de wijziging; dat is niet aangetoond en het vermoeden rust alleen op de redenering dat ook poly2grid zo'n blok null geeft. Kruiscontrole: mijn eigen `uitdraaiWB` op BAU geeft het landelijke totaal als 497,02305894898984 mln m3, tot op de kubieke meter hetzelfde, langs een ander item en op een andere werkkopie. Rest: dezelfde toets op de zichtjaarvariant, die een eigen `PerNL` heeft |
| 20 | #717 fractietak naast de klassetak | geslaagd, en de kernbevinding is gereproduceerd | Vers op beide varianten. Het groenaanbod gaat in de klassetak van 27.657,31 m2 in BAU naar 21.849,94 in NbSGenuanceerd, dus 21,0 procent omlaag, en in de fractietak van 38.899,76 naar 83.233,66, dus 114,0 procent omhoog. Het teken klapt dus om tussen de twee telwijzen, precies zoals #717 stelt, en dat is nu op verse standen van beide varianten gemeten in plaats van op de standen van augustus. Relevant groen: klasse 634.718,81 ha in BAU en 641.034,56 in NbSGenuanceerd, fractie 2.380.111,22 en 2.546.759,10. De druktegecorrigeerde maat klapt niet om: groen per woning gaat in de klassetak van 12.232,77 naar 12.875,32 m2, dus licht omhoog |
| 21 | #717 leverkant | gezakt, gerepareerd in 808639b4 | De doorlaat `BereikbaarheidGroen_Fractie.` eindigt op een punt en was geschreven voor de opgeschoonde naam, terwijl de toets op de ruwe naam draait. Van de 22 groenkaarten kwam er een doorheen. Na de reparatie drie, precies de fractiekaarten, en de klassevariant en de druktegecorrigeerde variant blijven eruit |
| 22 | #696 nieuwe natuur in de groenindicator | geslaagd als meting, hermeting gedaan | Vers op beide varianten, dus inclusief de hermeting die na #660 nodig was. BAU: 5.893,31 van 303.478,69 ha nieuwe natuur telt in de klassebenadering als groen, 1,94 procent. NbSGenuanceerd: 3.213,94 van 412.974 ha, 0,78 procent. De variant die het meeste nieuwe natuur maakt ziet daar dus relatief het minste van terug in de klassetak, wat het artefact uit #717 nog eens onderstreept |
| 23 | #720 piekbuidekking uitgesplitst | geslaagd als meting, en de klemming is nu gekwantificeerd | Vers op beide varianten. De vraag is in allebei 497,02305894898984 mln m3, want die hangt aan het basisjaar en is op bestaand bebouwd gebied gemaskeerd. `aanbod_op_wbcellen` is in allebei exact 0, zoals de toets voorschrijft: gealloceerde bergingscellen tellen per constructie niet mee. Het aanbod gaat van 38,17 mln m3 in BAU naar 292,79 in NbSGenuanceerd, bijna acht keer zoveel. Twee posten eten dat op. Van die 292,79 ligt maar 142,45 binnen bestaand bebouwd gebied, dus 51 procent van het aanbod kan per constructie geen vraag dekken. En de klemming op blokken van 500 meter kost in NbSGenuanceerd 114,17 mln m3 tegen 13,05 in BAU (restvraag ongeklemd 204,23 tegen geklemd 318,41). De dekkingsgraad komt daarmee op 5,1 procent in BAU en 35,9 procent in NbSGenuanceerd. Dat de klemverliezen meegroeien met het aanbod was bekend; dit is de eerste keer dat het voor beide varianten op een verse stand staat |
| 24 | #632 en #693 tabeltoevoegingen | geslaagd | `Bereikbaarheid_Banen` staat met een concreet kind in de ExplicitSuppliers, dus de valkuil dat een container niet meelift is vermeden. De claimrealisatie komt per schaalniveau mee, met de niveaus naast elkaar zodat overflow zichtbaar wordt |

## Voetafdruk en de vorige toetsronde

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 25 | #716 equivalentie van de voetafdrukketen | geslaagd | Drie uitdraaien op nul voor alle zes de werksubsectoren en voor wonen |
| 26 | #716 tegenover het doel van het issue | doel niet gehaald | De klem op het celoppervlak die de startstand wel heeft en de iteratie-update en de afleiding niet, is niet gebouwd. De cellen boven het celoppervlak bestaan nog |
| 27 | #714 werklijst | geslaagd, maar bevroren | Bruikbaar instrument omdat het per rij de hardheid van het bewijs vastlegt, maar bevroren op een codestand die dezelfde dag door negen gedragswijzigende commits is ingehaald. Vintagewaarschuwing toegevoegd in b023a4c7 |

## Wat de verse standen laten zien

Beide zichtjaren van 2040 zijn opnieuw doorgerekend, elf stappen met exit 0 en nul foutregels.

| maat | BAU | NbSGenuanceerd |
|---|---|---|
| claimrealisatie wonen, NL | 1,0007 | 0,9984 |
| claimrealisatie wonen, 76 NVM-regio's | min 0,9490, max 1,0565 | niet uitgesplitst |
| claimrealisatie banen, NL | 1,0186 | 1,0178 |
| claimrealisatie waterberging | leeg, geen opgave | 0,9994 tot 1,0000 over vijf regio's |
| nieuwe natuur | 303.478,7 ha | 412.974,0 ha |
| verstedelijking | 29.844,8 ha | 36.590,9 ha |
| inbreidingsaandeel | 0,5714 | 0,4982 |
| waterberging op veen | 0 ha | 2.872,2 ha |
| verdwenen natuur | 1.154,1 ha | 494,6 ha |

De banenoverschrijding is met #667 van 1,0489 naar 1,0186 gegaan, tegenover de controleronde van 24 en 25 augustus. NbSGenuanceerd verstedelijkt 6.746 ha meer dan BAU terwijl de woningclaim daar niet hoger ligt, en het inbreidingsaandeel zakt van 0,57 naar 0,50; dat is het ruimtebeslageffect van de dichtheidsfactoren uit #715, hier voor het eerst op verse standen van beide varianten naast elkaar.

Nieuw gevonden op de verse grondbalans: de driedeling sluit in geen van beide varianten helemaal. In BAU is verstedelijking 3.865,75 plus nieuwe natuur 26.982,38 plus waterberging 0, min 20,19 overlap, oftewel 30.827,94 tegen een verlies van 30.866,06 ha; er blijft 38,12 ha over, 0,12 procent. In NbSGenuanceerd is het 6.368,88 plus 76.104,56 plus 1.168,50, min 40,06 overlap, oftewel 83.601,88 tegen een verlies van 83.643,69 ha; daar blijft 41,81 ha over, 0,05 procent.

Die twee resten zijn in hectares vrijwel gelijk terwijl het verlies zelf een factor 2,7 verschilt. Het is dus geen systematische fout die met het verlies meeschaalt, maar een vaste post van ongeveer veertig hectare die naar een vierde bestemming gaat. De drie bestemmingsindicatoren zijn deelverzamelingen van het verlies, dus dat kan; alleen heeft die restcategorie geen naam, en de toelichting bij de indicator suggereert dat de drie samen het verlies dekken. In BAU komt het net boven de grens van een tiende procent waarboven de toetsprocedure een bevinding wil zien.

## Stand

| oordeel | aantal |
|---|---|
| geslaagd | 12 |
| geslaagd, met een randgeval of alleen aan de rekenkant | 5 |
| gezakt, inmiddels gerepareerd | 2 |
| gezakt als meetinstrument | 2 |
| doel niet gehaald | 4 |
| open | 2 |

Twee reparaties zijn uit deze ronde voortgekomen en gecommit: fe317807 voor de standlegenda en 808639b4 voor de doorlaat in het opleveringsscript. Een derde, de kolomnamen in `Diagnose684`, is door sessie 8f gedaan in 59998b98.

## Wat er niet is getoetst

- Een volledige reeks zichtjaren. De legendafix repareert alleen de schrijfkant, dus de standen Y2050 tot en met Y2120 uit de productierun blijven geweigerd en een reeks moet vanaf Y2040 opnieuw. Dat is ongeveer zeven uur per variant.
- Of de zichtjaargeschiktheid struikelt op de 26 hernoemde opbrengstenbestanden.
- Of de waterberging in NbSGenuanceerd op de 9a-vlakken landt.
- Het verschil tussen poly2grid en modus in de piekbui-indicator.
- Of de woningtype-as in #673 de keuze tussen ontwikkelpakketten verzet.

Ronde 3, de container `Diagnose/Ongemeten` voor beide varianten, liep bij het schrijven van deze lijst nog. De rijen 20 tot en met 23 dragen daaruit al de BAU-getallen; de NbSGenuanceerd-kant volgt.
