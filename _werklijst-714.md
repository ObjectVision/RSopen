# Werklijst toetsing #714

Achtendertig wijzigingen tussen commit 9d0b0f08 (27 augustus, de stand die in #639 is getoetst) en nu. Per wijziging het oordeel en waarop dat rust.

Oordelen: **geslaagd** is gemeten en het getal klopt met wat de wijziging beloofde. **gezakt** is gemeten en het klopt niet. **zwak** is wel een getal maar zonder referentie om het tegen af te zetten. **deels** is een van de twee helften getoetst. **open** is niet gemeten.

Bijgewerkt: 30 augustus, na de sorteerhoist-A/B en de IJburg2-meting.

## Rekenkern en rekenpad

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 1 | 529e40a4 Seq_1 op vijf iteraties | geslaagd, met nuance | A/B 5 tegen 15: 3.897 woningen op 9,5 miljoen, 0,041 procent. Regionale spreiding tot op zeven decimalen identiek, dus de extra iteraties helpen de tekortregio's niet. Geen meetbare tijdwinst, dus de wijziging levert ook niets op |
| 2 | ccb31b4c voetafdruk langs einde-jaars afleiding | gezakt | Equivalentietoets geeft 3.295, 4.490 en 13.565 m2 verschil voor detailhandel, overige consumentendiensten en overheid. 1,77 procent absoluut, 0,74 procent netto. Oorzaak aanwijsbaar, zie #714 en #716 |
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
| 11 | #670 MinimumSubsectorShare uit de zeef | open, nulmeting | Basisjaarzeef per subsector nu meetbaar: nijverheid 1.743.391 ha, logistiek 1.745.991, de vier overige alle vier 1.627.149. Maar #670 werkt op de zichtjaarzeef, dus dit is nog geen toets |
| 12 | #669 omgekeerde milieuzonering begrensd | open, nulmeting | Idem: de basisjaarzeef is gemeten, de zichtjaarzeef waar de zonering werkt nog niet |
| 13 | #668 thuiswerkverdikking op de ruimtevraag | open | Geen controle in de configuratie |

## Wonen: prijs, kosten en zeef

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 14 | #674 verwervingskosten op kentallen | zwak | Alleen indirect via het inbreidingsaandeel; geen referentie |
| 15 | #675 bouwperiode in de voorraadprijs | geslaagd | Term ongelijk nul voor alle vier de woningtypen, van -0,083 tot -0,105 over 8,34 miljoen objecten. exp(-0,0865) min 1 is min 8,3 procent, het gedocumenteerde effect |
| 16 | #676 guard op de lnlotsize-term | open | Geen controle |
| 17 | #677 pakketwater in de natuurterm | geslaagd | Harnas Diagnose677: opslag per woningtype van -25,5 tot +95,9 procent, met pakketgroen tot +152 procent |
| 18 | #678 groenwaarde als verandering | zwak | Getal beweegt, maar de referentie uit #639 is door de zichtjaarwissel niet meer vergelijkbaar |
| 19 | #700 vbo-bovengrens alleen voor wonen | geslaagd | Oude regel hield 180,4 van 520,2 miljoen m2 over. Afgeleide bouwlagen 1,13 logistiek tot 2,29 zakelijke dienstverlening |
| 20 | #702 groenfracties gemaskeerd | geslaagd | Eigen IntegrityCheck all(this <= 1.001f) vuurde in elke run zonder te falen |
| 21 | #703 BAG-nieuwbouw ontdubbeld | geslaagd | 540.949,5 woningen gemeten tegen 540.950 in het commitbericht. De dubbeltelling zat vooral aan de werkkant, banen van 395.804 naar 318.210; aan de woonkant heffen de weggehaalde dubbeltelling en de nieuwe splitsingenroute elkaar grotendeels op |
| 22 | #686 zeerharde restricties apart | geslaagd | zeef_verlies nul voor wonen en werken in beide varianten; de schakelaar staat uit, dus inert zoals bedoeld. Wat hij zou kosten: 585,9 ha wonen en 2.146,4 ha werken |
| 23 | #685 zeeftoets NbSGenuanceerd-pakketten | open | Geen controle |
| 24 | #620 kansrijke locaties in de trede | open | Geen controle; de sloopkant van #620 is wel getoetst |

## Natuur, veen en sloop

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 25 | #660 veennatuur vervangt bestaande natuur | geslaagd | Tekort van 87.409 ha (33,8 procent) naar 5.096 ha (2,39 procent). Afgedwongen deel van 89,2 naar 14,5 procent, krappe peilvakken van 4.294 naar 585 |
| 26 | #620 sloop volgt de oplegging niet | geslaagd | BAU sloopt nul en spaart 25.048 woningen; twaalf sloopkaarten met som nul zijn daarvan het gevolg |
| 27 | #707 kustregime van slopen naar niet bouwen | geslaagd | 2.369,2 woningen voor, 0 na, over 49.424 ha |
| 28 | #657 veenreserve en koolstofboekhouding | geslaagd | Stroom per periode telt op tot de cumulatieve stand: -17,34 en -9,87 tegen -27,21 Mton. Veenreserve 221.448 van 438.667 ha veenbodem |
| 29 | #698 hoge gronden | geslaagd | 1.819.410 ha tegen de gedocumenteerde 1.820.435, en 51,9 procent van het studiegebied |
| 30 | #699 naaldbos hoog, loofbos laag | open | Geen controle |
| 31 | #658 sloop naar drie oorzaken | geslaagd | Drieluik telt op tot het totaal en sluit kruiselings met de variantdatakant |

## Waterberging, schade en verharding

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 32 | 52f4565b varianttabel opnieuw ingeregeld | deels | Veertien parameters veranderd. De dichtheidsfactoren zijn als oorzaak van 45.000 ha extra verstedelijking in beeld en staan als vraag in #715. De rest niet getoetst |
| 33 | #712 bouwwijze veen geldt voor pakketten | open | Geen controle |
| 34 | #681 schadefunctie verschuift langs de diepte-as | geslaagd | Nieuwbouwschade 34,63 miljard in BAU en 5,77 miljard in NbSGenuanceerd, niet langer nul. Legt tegelijk #687 bloot: op geen enkele nieuwbouwcel schrijft het pakket een waterbestendige bouwwijze voor |
| 35 | #697 verharding kan dalen | zwak | Getal beweegt de goede kant op maar zonder referentie |
| 36 | #665 bouwmethode en dieptevermogen als twee assen | open | Geen controle |

## Export en diagnose

| # | wijziging | oordeel | waarop het rust |
|---|---|---|---|
| 37 | #651 elf NCW-varianten in de exportlijst | geslaagd | Alle NCW-kaarten bewegen tegengesteld aan hun nominale tweeling, dus de verdiscontering werkt |
| 38 | #692 casus en jaar in de bestandsnaam | geslaagd | Alle losse uitdraaien dragen het voorvoegsel; mijn toetsscript moest erop aangepast worden |

## Stand

Geslaagd 25, gezakt 1, zwak 3, deels 1, open 8.

De acht open punten hebben een gemeenschappelijke oorzaak: er bestaat geen enkele controle voor. Dat is geen tekort aan runs maar een tekort aan meetpunten, en de enige route is een check toevoegen of een A/B draaien.
