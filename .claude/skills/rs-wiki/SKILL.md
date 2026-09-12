---
name: rs-wiki
description: Schrijven op de RSopen-wiki; waar de wiki staat, hoe je pusht, de schrijfstijl, welke kennis op een indicatorpagina hoort tegenover een toepassingspagina, hoe je een pagina naast de code legt, figuren, en hoe de PriceIndices-wiki eraan hangt. Gebruik bij elke wijziging aan de wiki, en wanneer je tijdens het toetsen merkt dat de wiki achterloopt op de code.
---

# Schrijven op de RSopen-wiki

De wiki is een naslagwerk over hoe het model werkt. Wie het model gebruikt zoekt daar de methode op,
niet de uitkomst van een bepaald project. Dat onderscheid bepaalt wat er op welke pagina hoort.

## Waar de wiki staat en hoe je pusht

GitHub: ObjectVision/RSopen/wiki. Markdown, in het Nederlands. `_Sidebar.md` is de navigatie,
`Home.md` de inhoudsopgave en `Effectmodules-en-indicatoren.md` de index van de indicatoren.

Werk in een verse kloon buiten de repo:

```bash
git clone https://github.com/ObjectVision/RSopen.wiki.git <scratchpad>/wiki
```

Staat er op de machine al een kloon, bijvoorbeeld in een tools-map naast de werkkopieen, gebruik die
dan alleen om te lezen, en kijk eerst met `git fetch` en `git log origin/master..master` of hij niet
voor- of achterloopt op de remote. Zo'n kloon is eerder een werkkopie met ongepusht werk gebleken:
lees hem dan niet als de stand van de wiki en push hem niet zonder te vragen.

Bewerken, committen, `git push origin master`. De remote wijzigt tussendoor doordat er ook via de
webinterface wordt geschreven. Bij een reject: `git pull --rebase origin master` en opnieuw pushen.
Bij een conflict is niet standaard een kant goed: kijk per bestand welke kant de code volgt. Op een en
dezelfde dag was de remote nieuwer voor de ene pagina en de lokale commit voor de andere. De
commitregels staan in de skill rs-issues; let bij een rebase op een onderwerpregel die met een hekje
begint, git gooit die zonder `--cleanup=whitespace` stil weg.

## Wat op welke pagina hoort

| Soort pagina | Wat er hoort |
|---|---|
| indicator of methode | hoe de indicator rekent, wat hij meet en wat niet, de aannames en de beperkingen |
| toepassing (een project) | welke varianten er zijn, welke instellingen die dragen, en de uitkomsten |

Variantnamen, schakelaarstanden en getallen zijn projectspecifiek. Ze horen thuis op de
toepassingspagina's, bijvoorbeeld [[Toepassing NL2120]].

Dat geldt ook voor welke sectoren, schakelaars en regels in de configuratie aan of uit staan. Een
kader bovenaan een methodepagina dat zegt dat zonne-energie, verblijfsrecreatie en windenergie
uitstaan, of dat de allocatietabel wonen, werken en waterberging draait, leest daar als een
eigenschap van het model. Beschrijf op de methodepagina het mechanisme, dus dat de sectorlijst in
ModelParameters de plek is waar een toepassing haar sectoren aan- en uitzet, en laat de invulling aan
de toepassingspagina. De toets per zin: zou deze zin nog kloppen als een ander project dit model
gebruikt? Zo niet, dan hoort hij op de toepassingspagina.

Op een indicatorpagina mogen projectwaarden wel voorkomen, maar alleen als voorbeeld dat de methode
illustreert, en dan moet dat er ook staan. Schrijf dus niet "de dakfractie is 0,70" maar "in de
NL2120-toepassing staat die fractie voor NbSGenuanceerd op 0,70; die waarde hoort bij het project en
niet bij de indicator". Zonder die formulering leest een volgende gebruiker een projectkeuze als een
modeleigenschap, en dat is precies wat een naslagwerk niet moet doen.

Dezelfde regel geldt voor meetuitkomsten. Een getal uit een run mag als illustratie op een
indicatorpagina staan, met de casus, het zichtjaar en de datum of de tag erbij, zodat duidelijk is
dat het een voorbeeld is en geen eigenschap.

## De PriceIndices-wiki hangt eraan

De schattingskant van het hedonische woningprijsmodel staat niet in RSopen maar in de repo
PriceIndices, onder een ander GitHub-account en met een eigen wiki. De arbeidsdeling is bewust:
PriceIndices beschrijft hoe de schattingen worden gemaakt (data, schoning, geocodering, spatial
variabelen, specificaties, output), de RSopen-wiki beschrijft het model zelf en de toepassing, op de
pagina Hedonisch-woningprijsmodel. Beide kanten linken naar elkaar met volledige GitHub-URL's, want
dubbele-haken-links werken niet over wiki's heen.

De brugpagina Koppeling-met-RuimteScanner op de PriceIndices-wiki somt op wat tussen de twee repo's
synchroon moet blijven: de natuur- en waterdefinitie (LGNKlasse.dms hier tegenover IsNatuur_hedonisch
daar), stralen, kernels en randcorrectie, de LGN-klassevolgorde in de _m25.tif, de hoogbouwgrens van
15 meter en de WP4-indeling. RSopen leest de gebruikte specificatie via NVM_filedate en
NVM_coeff_Year in ModelParameters.dms.

Bij een wijziging in de prijsfunctie of in de groenfracties werk je beide wiki's bij en loop je de
synchronisatietabel op de brugpagina na. Let daarbij op de valkuil dat referentieniveaus met
coefficient 0 in de estimates moeten staan; ontbreken ze, dan geeft rlookup aan de GeoDMS-kant een
null-prijs.

## Schrijfstijl

Geen vetgedrukte woorden binnen een zin. Kopjes met `##` en `###` zijn gewoon goed, en een vetgedrukt
woord als los label in de lopende tekst kun je beter ook vermijden.

Geen gedachtenstreepjes, dus geen em dash of en dash als leesteken. Herschrijf de zin, of gebruik een
komma, een dubbele punt, haakjes of een punt. Home.md en _Sidebar.md gebruiken gedachtenstreepjes als
scheidingsteken in lijstregels; dat is layout en geen prozapunctuatie, laat die staan.

Geen persoonsnamen. Verwijs naar de organisatie: Deltares, PBL, Object Vision, VU. De wiki is
openbaar, net als de repo.

Verwijs naar issues met een hekje, dus #634, zodat GitHub de koppeling legt.

## De wiki loopt achter op de code

Dat is de normale toestand, niet de uitzondering. De code verandert dagelijks, de wiki niet.

Bij een verschil is de code leidend voor wat er werkelijk is gerekend. Het verschil zelf is een
bevinding die op de pagina thuishoort, niet alleen in een chat of een issue. Werk de pagina dus bij
zodra je het verschil vaststelt; dat is goedkoper dan het onthouden.

Twee vormen die vaak voorkomen. Een parametertabel die een waarde noemt die inmiddels anders staat,
en een beschrijving van een mechanisme dat door een issue is vervangen. Bij het tweede is het niet
genoeg om het getal te wijzigen: dan moet de alinea eromheen mee, anders blijft de oude redenering
staan onder een nieuw getal.

Een pagina die een ontwerp beschrijft veroudert bij het eerste ontwerpbesluit. Schrijf hem pas als
het besluit vastligt, of loop hem na bij elke reactie van de opdrachtgever.

### Een pagina naast de code leggen

"Staat het al op de wiki" is niet dezelfde vraag als "is het vindbaar". Controleer ook `_Sidebar.md`
en `Home.md` en niet alleen de inhoud met grep; de hedonische prijsfunctie stond maanden als
subparagraaf onderaan een sectorpagina zonder link vanuit de navigatie.

Begin een controleronde met twee scriptjes: haal alle identifiers tussen backticks uit de pagina en
zoek ze in alle dms-tekst van `cfg`, en toets elke `[[wikilink]]` tegen de bestandsnamen in de
kloon. Dat vangt verwijderde items, verzonnen namen en dode links.

Wat het niet vangt: een pagina die met de juiste namen een verouderde formule beschrijft, en een
mechanisme dat voor deze sector is uitgeschakeld. Zo'n sectie leest gezond terwijl de zeef die zij
beschrijft voor die sector niet bestaat. Zoek daarvoor per bewering op waar zij vandaan komt, en ga
bij een sectorgeneriek sjabloon na of de term een sectorpoort draagt, zoals IsThisSectorWonenOfWerken,
IsLandbouw of IsThisSectorWind.

## Illustraties

Figuren staan als png in de wikirepo, naast de pagina's; de generatorscripts horen in de scratchpad
en niet in de wiki. Echte data voor kaarten en grafieken staat in `%LocalDataProjDir%` (de
txt-exports van het Diagnose-harnas en de indicator-tifs per casus). Welke tekentools er op een
machine staan verschilt; controleer dat eerst.

Teken je met PIL, gebruik dan supersampling (factor 4 tekenen, verkleinen met LANCZOS bij opslaan),
want PIL heeft geen antialiasing. Een indicatorkaart uit een 25m-tif niet middelen naar de
figuurresolutie, dat poetst een dunne indicator weg: lees blokgewijs, neem per uitvoerpixel nanmax en
nanmin en houd de sterkste van de twee. Ondergrond: de unie van de NVM-regio's met
`buffer(250).buffer(-150).simplify(120)`, anders blijven er slivers tussen de regio's staan.
Kleurschaal op het 95e percentiel van de cellen met een waarde. Een schema dat een mechanisme toont,
zoals waar een restclaim landt, werkt met een paar regio's in echte vorm en pijlen; een choropleth
van het hele land hoort bij de indicator die hij toont, niet bij de uitleg van het mechanisme.

## Voordat je een uitkomst interpreteert

Lees de wikipagina van de indicator voordat je een conclusie trekt uit een getal. Zie de skill
rs-toetsen, laag 1b, voor de valkuilen die dat op 1 september 2026 opleverde: vier van de zes
kernconclusies over een productierun draaiden om zodra de wikipagina erbij werd gehaald.
