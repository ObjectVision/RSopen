# Werklijst toetsing #714

Achtendertig wijzigingen tussen commit 9d0b0f08 (27 augustus, de stand die in #639 is getoetst) en nu. Per wijziging het oordeel en waarop dat rust.

Oordelen: **geslaagd** is gemeten en het getal klopt met wat de wijziging beloofde. **gezakt** is gemeten en het klopt niet. **zwak** is wel een getal maar zonder referentie om het tegen af te zetten. **deels** is een van de twee helften getoetst. **open** is niet gemeten.

Bijgewerkt: 30 augustus, na de verse equivalentietoets.

## Rekenkern en rekenpad

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 1 | 529e40a4 Seq_1 op vijf iteraties | geslaagd, met nuance | A/B 5 tegen 15: 3.897 woningen op 9,5 miljoen, 0,041 procent. Regionale spreiding tot op zeven decimalen identiek, dus de extra iteraties helpen de tekortregio's niet. Geen meetbare tijdwinst, dus de wijziging levert ook niets op |
| 2 | ccb31b4c voetafdruk langs einde-jaars afleiding | geslaagd na reparatie, met restwaarde | Eerste toets gaf 3.295, 4.490 en 13.565 m2 verschil voor detailhandel, overige consumentendiensten en overheid, 1,77 procent absoluut en 0,74 procent netto. Oorzaak: de werkentak hing aan een sectorneutrale vlag terwijl #710 sinds 29 augustus verzorgende banen met het woonpakket laat meekomen. Gerepareerd in ce457501 en opnieuw getoetst: het maximumverschil staat nu op 625 m2 bij dezelfde drie subsectoren en op nul bij de andere drie en bij wonen. Die 625 is exact het celoppervlak op 25 meter en past bij de klemasymmetrie die #716 beschrijft, niet meer bij #710. De geleverde standen van 30 augustus zijn nog met de oude code gedraaid; dat is een bewuste keuze, met de richting per indicator benoemd in het opleveringsrapport |
| 3 | d410d3cd sorteerhoist werkgeschiktheid | geslaagd | A/B met de hunks omgekeerd: nul verschil op alle 48 controles, inclusief de regiolijsten. Exact gedragsneutraal |
| 4 | 991031df tie-break IJburg2 | geslaagd | 3.584 cellen, 55,6 woningen in het basisjaar en 5.604,2 in Y2040, dus 5.548 nieuwe woningen op 224 ha. De zone valt niet uit de allocatie, wat de tie-break moest voorkomen |
| 5 | fe9b7f15 vijftien ketens ontkoppeld naar BaseData | geslaagd, met steekproef | Alle 33 fingerprints vers geschreven in deze ronde, dus geen verouderd bestand heeft meegedaan. Zes van de 33 inhoudelijk bekeken: ze dragen naast bronvintage en studiegebied ook de inhoudelijke drempels, zoals buffer_wonen_m, milieucat_count en vol_fraction. Zeven BGT-afgeleiden hebben geen fingerprint; die zijn geldig omdat bgt.dms sinds 20 augustus onveranderd is, maar dat moest met de hand tegen git |
| 6 | ffaf93aa Opbrengsten_perOP per set | geslaagd | 28 van de 53 tifs byte-identiek tussen BAU en NbSGenuanceerd, 25 verschillend. De toelichting claimt exact 25 |

## Claims

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 7 | #667 claimanker en combi-uitsplitsing | geslaagd | Landelijke banenrealisatie van 1,0714 naar 1,0182. Onvermijdelijk overschot van 537.442 naar 301.786. Zak_dienstverlening van 1,2010 naar 1,0045, regio's boven de stand van 76 naar 46 |

## Werken

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 8 | #709 greenfield-vrijstelling expliciet | geslaagd, op een codeargument | Voor: de toets vergelijkt Result gedeeld door StateSectorVoorAllocatie met een drempel. Op greenfield is die noemer nul, dus de deling geeft oneindig, NaN of null, en elke vergelijking daarvan geeft FALSE. Na: de toets vuurt alleen bij WerkstandVoorAllocatie groter dan nul, wat op greenfield ook FALSE geeft. Dezelfde uitkomst, expliciet in plaats van impliciet. Dit is redenering en geen meting |
| 9 | #710 verzorgend werken volgt wonen | geslaagd | Aandeel in bebouwd gebied van 14 tot 32 procent naar 39,6 tot 48,1 procent. Verlies aan verzorgende banen van 135.924 naar 31.220 |
| 10 | #713 sloopwacht op hetzelfde deeloppervlak | geslaagd | Zelfde meting; alle zes de subsectoren binnen de band 0,98 tot 1,05 |
| 11 | #670 MinimumSubsectorShare uit de zeef | geslaagd | De verwijderde toets is nagebouwd naast de toets die ervoor in de plaats bleef, zonder hem ergens in te hangen. In Y2040 van BAU haalde de oude toets 133.583, 86.928 en 105.555 hectarecellen weg bij detailhandel, nijverheid en zakelijke dienstverlening, de dichtheidstoets 9.771, 34.240 en 2.721. Heropend zijn 127.551, 74.226 en 104.471 cellen, en daarop staat 1,94, 0,70 en 1,93 miljoen banen tegenover een potentieel van 5,78, 2,44 en 13,66 miljoen. Elke heropende cel is dus een netto winst, wat de claim van #670 was. De 34.240 komen exact overeen met het getal dat #713 voor nijverheid noteert, dus de nabouw leest hetzelfde item. Wat #670 wel opgeeft is de identiteitsrem: een subsector kan nu een cel overnemen waar hij nul aandeel heeft, mits het saldo verbetert |
| 12 | #669 omgekeerde milieuzonering begrensd | geslaagd | Meetpunt in de allocatie zelf, waar de oude en de nieuwe toestand naast elkaar staan, dus zonder A/B. Bufferbron 4.487.408 wooncellen tegen 3.948.086 cellen aaneengesloten woongebied, dus 12,0 procent eraf. Bestaand werkterrein 1.268.033 cellen, met de banenregel 1.820.507 en 1.734.853. Blijft dicht: 30,7 procent van het studiegebied voor nijverheid en 15,8 procent voor logistiek, tegen de 29,1 procent die de parametertoelichting op de basisjaarstand noemt |
| 13 | #668 thuiswerkverdikking op de ruimtevraag | geslaagd | De pathologie die de schakelaar veroorzaakte is weg: zakelijke dienstverlening staat in Y2040 op 2.047.812 banen tegen een claim van 2.069.520, en 27 van de 76 NVM-regio's hebben nog restclaim. Met de schakelaar aan was dat 2.437.320 tegen 2.018.666 en nul regio's. De bedoelde route klopt rekenkundig: kantoorcoefficient 17,5 tegen 20 in het basisjaar geeft groeifactor min 0,125, dus voetafdruk per kantoorbaan maal 0,875 en banen per m2 maal 1,1429 |

## Wonen: prijs, kosten en zeef

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 14 | #674 verwervingskosten op kentallen | zwak | Alleen indirect via het inbreidingsaandeel; geen referentie |
| 15 | #675 bouwperiode in de voorraadprijs | geslaagd | Term ongelijk nul voor alle vier de woningtypen, van -0,083 tot -0,105 over 8,34 miljoen objecten. exp(-0,0865) min 1 is min 8,3 procent, het gedocumenteerde effect |
| 16 | #676 guard op de lnlotsize-term | geslaagd | De commit draagt de meting: cellen met voorraad en een ongedefinieerde prijs gingen bij appartementen van 4.156 naar 421, bij de drie eengezinstypen bleef het 2, 12 en 0. De 435 resterende nullen hebben een andere oorzaak en staan los van dit issue |
| 17 | #677 pakketwater in de natuurterm | geslaagd | Harnas Diagnose677: opslag per woningtype van -25,5 tot +95,9 procent, met pakketgroen tot +152 procent |
| 18 | #678 groenwaarde als verandering | zwak | Getal beweegt, maar de referentie uit #639 is door de zichtjaarwissel niet meer vergelijkbaar |
| 19 | #700 vbo-bovengrens alleen voor wonen | geslaagd | Oude regel hield 180,4 van 520,2 miljoen m2 over. Afgeleide bouwlagen 1,13 logistiek tot 2,29 zakelijke dienstverlening |
| 20 | #702 groenfracties gemaskeerd | geslaagd | Eigen IntegrityCheck all(this <= 1.001f) vuurde in elke run zonder te falen |
| 21 | #703 BAG-nieuwbouw ontdubbeld | geslaagd | 540.949,5 woningen gemeten tegen 540.950 in het commitbericht. De dubbeltelling zat vooral aan de werkkant, banen van 395.804 naar 318.210; aan de woonkant heffen de weggehaalde dubbeltelling en de nieuwe splitsingenroute elkaar grotendeels op |
| 22 | #686 zeerharde restricties apart | geslaagd | zeef_verlies nul voor wonen en werken in beide varianten; de schakelaar staat uit, dus inert zoals bedoeld. Wat hij zou kosten: 585,9 ha wonen en 2.146,4 ha werken |
| 23 | #685 zeeftoets NbSGenuanceerd-pakketten | geslaagd | Meting685 per ontwikkelpakket, beide kanten op. In BAU staan alle Max- en alle Nuanceerd-pakketten op nul beschikbare cellen terwijl de gewone pakketten er 1.514 tot 24 miljoen hebben. In NbSGenuanceerd is het omgekeerd: de vier Nuanceerd-eengezinspakketten hebben 180.724 tot 9.781.229 cellen en de vijf Max-pakketten nul. Dat is de dubbeling in de OR-lijst die de Nuanceerd-toets dode code maakte |
| 24 | #620 kansrijke locaties in de trede | geslaagd, met nuance | Het zoekgebied is 56.582 ha, waarvan 39.314 ha buiten bestaand bebouwd gebied. Daar stonden 21.940 woningen in het basisjaar. In Y2040 staan er 37.959 in BAU en 49.555 in NbSGenuanceerd, terwijl de landelijke groei in NbSGenuanceerd juist lager is. Het zoekgebied vangt 1,15 procent van de landelijke groei in BAU en 2,11 procent in NbSGenuanceerd, dus 1,84 keer zoveel. De tredestap stuurt. Nuance: alleen NbSGenuanceerd kent de dimensie, en die variant verschilt op meer dan dit, dus dit is geen zuivere A/B |

## Natuur, veen en sloop

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 25 | #660 veennatuur vervangt bestaande natuur | geslaagd | Tekort van 87.409 ha (33,8 procent) naar 5.096 ha (2,39 procent). Afgedwongen deel van 89,2 naar 14,5 procent, krappe peilvakken van 4.294 naar 585 |
| 26 | #620 sloop volgt de oplegging niet | geslaagd | BAU sloopt nul en spaart 25.048 woningen; twaalf sloopkaarten met som nul zijn daarvan het gevolg |
| 27 | #707 kustregime van slopen naar niet bouwen | geslaagd | 2.369,2 woningen voor, 0 na, over 49.424 ha |
| 28 | #657 veenreserve en koolstofboekhouding | geslaagd | Stroom per periode telt op tot de cumulatieve stand: -17,34 en -9,87 tegen -27,21 Mton. Veenreserve 221.448 van 438.667 ha veenbodem |
| 29 | #698 hoge gronden | geslaagd | 1.819.410 ha tegen de gedocumenteerde 1.820.435, en 51,9 procent van het studiegebied |
| 30 | #699 naaldbos hoog, loofbos laag | geslaagd | De huidige en de omgekeerde toewijzing staan naast elkaar in de code, dus beide zijn uit te rekenen. Het boomdeel van de pakketten ligt vrijwel evenredig verdeeld: 1.490 ha hoog tegen 1.372 ha laag in BAU. De omkering zou de vastlegging met 153,6 ton per jaar en de voorraad met 3.899 ton verhogen; in NbSGenuanceerd is dat 774,2 en 19.653 ton bij 4.449 tegen 3.854 ha. Beide getallen sluiten exact op de kengetallen, 1,3 respectievelijk 33 ton per hectare maal het areaalverschil, wat bewijst dat de opzoeking de goede rijen raakt. De richting is dus juist en de omvang is verwaarloosbaar: 3.899 ton is 0,014 procent van de koolstofuitkomst |
| 31 | #658 sloop naar drie oorzaken | geslaagd | Drieluik telt op tot het totaal en sluit kruiselings met de variantdatakant |

## Waterberging, schade en verharding

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 32 | 52f4565b varianttabel opnieuw ingeregeld | deels | Veertien regels aangeraakt, waarvan twee alleen witruimte. Vijf hebben gedragsgewicht. De dichtheidsfactoren gingen in NbSGenuanceerd terug van 1,30/1,70/1,40 naar de waarden van de andere varianten, wat de 45.000 ha extra verstedelijking verklaart en als vraag in #715 staat. SuperStedelijkToegestaan ging in beide NbS-varianten aan, en dat is meetbaar via Meting685. GevaarRegimeZone2 werd in NbSGenuanceerd soepeler, van bouwen met maatregelen naar bouwen. De dakfracties ruilden groen voor blauw in de NbS-varianten, 0,40 groen naar nul tegen 1,00 en 0,70 blauw. De wadi-fractie in BAU ging van 0,05 naar 0,10. Geen van de vijf is een fout, alle vijf zijn keuzes; alleen de dichtheidsfactoren zijn doorgemeten |
| 33 | #712 bouwwijze veen geldt voor pakketten | geslaagd | Dezelfde uitdraai als #685 draagt de twee veenkolommen. In BAU staat de schakelaar uit en zijn beide nul. In NbSGenuanceerd zeeft de bodemdalingstoets 2.835.533 cellen weg bij de pakketten die niet bodemdalingbestendig zijn en nul bij de pakketten die dat wel zijn; de drijvendtoets doet hetzelfde met 938.387 cellen. Op die laatste cellen blijft NuanceerdLNLLaagVS over, dus er is daar nog een pakket toegestaan en de toets sluit het gebied niet volledig af |
| 34 | #681 schadefunctie verschuift langs de diepte-as | geslaagd | Nieuwbouwschade 34,63 miljard in BAU en 5,77 miljard in NbSGenuanceerd, niet langer nul. Legt tegelijk #687 bloot: op geen enkele nieuwbouwcel schrijft het pakket een waterbestendige bouwwijze voor |
| 35 | #697 verharding kan dalen | geslaagd | De verharding daalt werkelijk, en dat kon voor deze wijziging niet. In Y2040 van BAU daalt hij op 383.066 cellen en stijgt hij op 488.115, goed voor 5.908 tegen 11.294 hectare, dus netto nog 5.386 hectare erbij. In NbSGenuanceerd kantelt het: 1.312.307 cellen omlaag tegen 650.249 omhoog, 16.776 tegen 7.602 hectare, dus netto 9.174 hectare verharding minder dan in het basisjaar. Dat is precies het gedrag dat de wijziging mogelijk moest maken en dat de NbS-variant hoort te laten zien |
| 36 | #665 bouwmethode en dieptevermogen als twee assen | geslaagd | De commit draagt zijn eigen gouden waarden: BouwwijzeK/Controle/Origineel legt de vier afgeleide kolommen naast de literalen van voor de splitsing, met vijf IntegrityChecks. Dat item gedraaid: exitcode 0, geen fout, dus alle vijf houden stand en de splitsing is gedragsneutraal |

## Export en diagnose

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 37 | #651 elf NCW-varianten in de exportlijst | geslaagd | Alle NCW-kaarten bewegen tegengesteld aan hun nominale tweeling, dus de verdiscontering werkt |
| 38 | #692 casus en jaar in de bestandsnaam | geslaagd | Alle losse uitdraaien dragen het voorvoegsel; mijn toetsscript moest erop aangepast worden |

## Stand

Geslaagd 34, gezakt 0, zwak 3, deels 1, open 0.

Er staan geen open punten meer. De zes die er waren zijn gesloten door meetpunten toe te voegen op plekken waar de oude en de nieuwe toestand naast elkaar in de code staan, zodat er geen tweede run met omgezette code nodig was. Dat was ook de diagnose: het was geen tekort aan runs maar een tekort aan meetpunten.

De gezakte toets, de voetafdrukafleiding, is gerepareerd en de verse equivalentietoets heeft dat bevestigd. Wat overblijft is een restwaarde van 625 m2, exact het celoppervlak, bij dezelfde drie subsectoren; die hoort bij de klemasymmetrie uit #716 en niet meer bij de oorzaak die hier is weggenomen.

Wat overblijft zijn drie zwakke oordelen en een deels. Zwak betekent hier dat het getal beweegt zoals verwacht maar dat er geen onafhankelijke referentie naast ligt; bij #674 is die er wel in de vorm van een IntegrityCheck die het landelijk totaal tussen 250 en 900 miljard begrenst, en die vuurt in elke run.
