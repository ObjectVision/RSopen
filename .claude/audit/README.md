# Auditrollen

In `.claude/agents/` staan rollen die het model vanuit een vakgebied doorlichten. Elke rol is een
apart proces met een eigen contextvenster: ze zien elkaars werk niet en praten elkaar dus niet na.
Dat is precies de bedoeling, want vier rollen die onafhankelijk naar dezelfde configuratie kijken
vinden andere dingen dan vier keer dezelfde controle.

## De rollen

| rol | waarvoor |
|---|---|
| hydroloog | waterberging, peilvakken, capaciteit, SOMERS, vernatting |
| stadsecoloog | natuurtypen, samenhang van nieuwe natuur, groennabijheid, mortaliteit, koolstof |
| woningmarkteconoom | hedonisch prijsmodel, woningwaarde, dubbeltelling in waardering |
| planoloog | zeef, plancapaciteit, bouwregime, ontwikkelpakketten, samenhang tussen zichtjaren |
| grondeconoom | grondproductiekosten, verwerving, uitkoop en sloop, schade, eenheden en prijspeil |
| beleidsspiegel | uitlegbaarheid en bruikbaarheid, gelezen vanuit VRO en vanuit een gemeente |

Ze delen `briefing.md` in deze map. Daarin staan het model, de eigenaardigheden van GeoDMS waar
fouten zich verstoppen, de bewijsregel en de rapportvorm.

## Aanroepen

Noem de rol gewoon in je vraag:

```
laat de hydroloog de waterbergingsopgave van NbSGenuanceerd 2030 nalopen
zet de stadsecoloog en de hydroloog samen op de veenkant, ieder apart
planoloog: klopt de zeef nog na de wijziging van gisteren
```

Meerdere rollen tegelijk kan, ze draaien dan parallel. Met `/agents` zie en beheer je ze.

## Waar ze geladen worden

Deze rollen horen bij deze map. Werk je lokaal in een projectconfiguratie die ergens anders staat,
dan zijn er twee manieren: kopieer `.claude/agents` naar die map, of zet de bestanden in
`~/.claude/agents` zodat ze in al je projecten beschikbaar zijn. De briefing verwijst naar paden uit
de open configuratie en zegt er zelf bij dat je paden moet opzoeken en niet aannemen.

## Wat een rol wel en niet is

Een rol maakt van het model geen echte hydroloog. Hij stuurt de aandacht, het vocabulaire en vooral
de vragen die gesteld worden. De opbrengst is dekking en variatie, niet gezag.

Behandel elke bevinding daarom als hypothese tot hij is nagetrokken tegen de configuratie of tegen
gemeten getallen. De briefing dwingt dat af met de eis van een vindplaats bij elke bevinding en met
een aparte lijst voor vermoedens. Wat niet is nagetrokken gaat niet in een issue.

## Een rol toevoegen of aanpassen

Maak een nieuw bestand in `.claude/agents/` met deze kop:

```markdown
---
name: kortenaam
description: waarvoor deze rol is, want hierop wordt hij gekozen
tools: Read, Grep, Glob, Bash
---
```

Daaronder de rol zelf: wie je bent, dat je eerst `.claude/audit/briefing.md` leest, waar je kijkt en
wat je toetst. Houd de toetsen concreet en gericht op dit model. Een lijst algemene vragen levert
algemene antwoorden op.

Geen namen van personen in deze bestanden, ook niet als voorbeeld. De repo is openbaar.
