---
name: rs-wiki
description: Schrijven op de RSopen-wiki; waar de wiki staat, hoe je pusht, de schrijfstijl, en welke kennis op een indicatorpagina hoort tegenover een toepassingspagina. Gebruik bij elke wijziging aan de wiki, en wanneer je tijdens het toetsen merkt dat de wiki achterloopt op de code.
---

# Schrijven op de RSopen-wiki

De wiki is een naslagwerk over hoe het model werkt. Wie het model gebruikt zoekt daar de methode op,
niet de uitkomst van een bepaald project. Dat onderscheid bepaalt wat er op welke pagina hoort.

## Waar de wiki staat en hoe je pusht

GitHub: ObjectVision/RSopen/wiki. Markdown, in het Nederlands. `_Sidebar.md` is de navigatie,
`Effectmodules-en-indicatoren.md` is de index van de indicatoren.

Er staat een lokale kloon in `C:\ProjDir\_Tools\RSopen.wiki`, handig om te lezen. Werk voor een
wijziging niet daarin maar in een verse kloon buiten de repo:

```bash
git clone https://github.com/ObjectVision/RSopen.wiki.git <scratchpad>/wiki
```

Bewerken, committen, `git push origin master`. De remote kan tussendoor wijzigen doordat er via de
webinterface wordt geschreven. Bij een reject: `git fetch && git reset --hard origin/master`, de
bewerking opnieuw, commit, push. Controleer voor je begint of de lokale kloon en de verse kloon
verschillen; is dat zo, dan werk je met de verse.

## Wat op welke pagina hoort

| Soort pagina | Wat er hoort |
|---|---|
| indicator of methode | hoe de indicator rekent, wat hij meet en wat niet, de aannames en de beperkingen |
| toepassing (een project) | welke varianten er zijn, welke instellingen die dragen, en de uitkomsten |

Variantnamen, schakelaarstanden en getallen zijn projectspecifiek. Ze horen thuis op de
toepassingspagina's, bijvoorbeeld [[Toepassing NL2120]].

Op een indicatorpagina mogen ze wel voorkomen, maar alleen als voorbeeld dat de methode
illustreert, en dan moet dat er ook staan. Schrijf dus niet "de dakfractie is 0,70" maar "in de
NL2120-toepassing staat die fractie voor NbSGenuanceerd op 0,70; die waarde hoort bij het project en
niet bij de indicator". Zonder die formulering leest een volgende gebruiker een projectkeuze als een
modeleigenschap, en dat is precies wat een naslagwerk niet moet doen.

Dezelfde regel geldt voor meetuitkomsten. Een getal uit een run mag als illustratie op een
indicatorpagina staan, met de casus, het zichtjaar en de datum of de tag erbij, zodat duidelijk is
dat het een voorbeeld is en geen eigenschap.

## Schrijfstijl

Geen vetgedrukte woorden binnen een zin. Kopjes met `##` en `###` zijn gewoon goed, en een vetgedrukt
woord als los label in de lopende tekst kun je beter ook vermijden.

Geen gedachtenstreepjes, dus geen em dash of en dash als leesteken. Herschrijf de zin, of gebruik een
komma, een dubbele punt, haakjes of een punt.

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

## Voordat je een uitkomst interpreteert

Lees de wikipagina van de indicator voordat je een conclusie trekt uit een getal. Zie de skill
rs-toetsen, laag 1b, voor de valkuilen die dat op 1 september 2026 opleverde: vier van de zes
kernconclusies over een productierun draaiden om zodra de wikipagina erbij werd gehaald.
