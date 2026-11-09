# RSopen

RSopen is de open-sourceversie van RuimteScanner 2.0, een model dat verkent hoe het landgebruik in Nederland zich kan ontwikkelen. Het verdeelt de vraag naar ruimte voor wonen, werken, waterberging, natuur, landbouw en andere functies over het land, binnen beleidsmatige en fysieke randvoorwaarden, en rekent de effecten daarvan uit, zoals overstromingsschade, bereikbaarheid van groen en woningwaarde. Het model draait op [GeoDMS](https://github.com/ObjectVision/GeoDMS). RSopen is ontwikkeld door PBL Planbureau voor de Leefomgeving, samen met Object Vision, Deltares en de Vrije Universiteit Amsterdam.

## Documentatie

De [wiki](https://github.com/ObjectVision/RSopen/wiki) is het naslagwerk bij het model. Goede startpunten zijn:

- [Introductie](https://github.com/ObjectVision/RSopen/wiki/Introductie): geschiedenis, doel en positionering van het model
- [Modelstructuur op hoofdlijnen](https://github.com/ObjectVision/RSopen/wiki/Modelstructuur-op-hoofdlijnen): hoe de allocatie en de effectmodules samenhangen
- [Toepassinggebied](https://github.com/ObjectVision/RSopen/wiki/Toepassinggebied): wat je wel en niet met het model kunt
- [Scenario's en beleidsvarianten](https://github.com/ObjectVision/RSopen/wiki/Scenario%27s-en-beleidsvarianten)
- [Effectmodules en indicatoren](https://github.com/ObjectVision/RSopen/wiki/Effectmodules-en-indicatoren)
- [Installatie tutorial](https://github.com/ObjectVision/RSopen/wiki/Installatie-tutorial) en [Batchrun draaien](https://github.com/ObjectVision/RSopen/wiki/Batchrun-draaien): het model zelf draaien
- [Referenties](https://github.com/ObjectVision/RSopen/wiki/Referenties), met de systeembeschrijving van Koomen, Rijken en Claassens (2024)

## Status en gebruik

RSopen is onderzoekssoftware en volop in ontwikkeling. De uitkomsten zijn verkenningen onder aannames over scenario's en beleid, geen voorspellingen. De software komt zonder garantie en zonder aansprakelijkheid, zoals de artikelen 15 en 16 van de GPL v3 bepalen. Wie uitkomsten gebruikt voor een advies of een besluit, toetst ze zelf en vermeldt welke versie van het model is gebruikt: de tak en de commit of de tag.

## Aan de slag

1. Installeer een release van [GeoDMS](https://github.com/ObjectVision/GeoDMS/releases). De rekenruns gebruiken nu GeoDms20.23.1.m.
2. Kloon deze repo en kies de tak: `main` is de algemene versie, en elke toepassing heeft een eigen tak (zie hieronder).
3. Kopieer `cfg/main/ConfigSettings.dms.example` naar `cfg/main/ConfigSettings.dms` en vul de paden naar de brondata en naar LocalData in. Dat bestand staat niet in git.
4. Open `cfg/main.dms` in de GeoDMS GUI, of draai een batchrun.

De geografische brondata zit niet in deze repo en is deels niet openbaar. Neem voor toegang contact op met Object Vision of PBL. De [Installatie tutorial](https://github.com/ObjectVision/RSopen/wiki/Installatie-tutorial) beschrijft elke stap.

## Takken

`main` is de stam: generiek werk komt hier eerst. Een toepassing, zoals `NL2120`, `dgwb-stad` of `dgwb-veenweide`, heeft een eigen tak met eigen varianten en instellingen, en haalt `main` binnen. Wie de resultaten van een toepassing wil reproduceren, heeft die tak nodig.

## Vragen en fouten

Fouten, vragen en wensen gaan via de [issues](https://github.com/ObjectVision/RSopen/issues) van deze repo.

## Licentie

De code valt onder de [GNU GPL v3](LICENSE), de wiki onder [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Data en teksten van anderen houden hun eigen voorwaarden.
