# CLAUDE.md

Instructies voor Claude Code in deze repo.

## Issues aanmaken

Issues in deze repo zijn openbaar. Houd je aan de volgende conventies.

### Geen persoonsnamen

Noem geen echte namen van personen, niet in de titel, de body of de comments. Verwijs naar de organisatie: Deltares, PBL, Object Vision, VU. Dus "vraag vanuit Deltares" en niet de naam van de betreffende onderzoeker. Dit geldt ook voor namen die al elders in de repo of in de chat voorkomen.

### Geen vetgedrukte tekst in de lopende tekst

Gebruik vet alleen voor kopjes. Geen vetgedrukte woorden of zinsdelen binnen alinea's, opsommingen of tabelcellen.

### Geen gedachtenstreepjes

Gebruik geen gedachtenstreepjes (em dash of en dash als leesteken). Herschrijf de zin, of gebruik een komma, dubbele punt of punt.

## Schrijfstijl algemeen

De regel over gedachtenstreepjes geldt ook buiten issues, dus in commit messages, documentatie en antwoorden in de chat. Geen 'authored by Claude' in de comments/commit messages etc.

## Verwijzen naar issues en pull requests

Schrijf verwijzingen altijd met hekje, dus #634 en niet "issue 634". Dit geldt in issues en comments, maar vooral ook in commit messages: zonder hekje herkent GitHub de verwijzing niet en verschijnt de commit niet in de tijdlijn van het issue.

Begin de onderwerpregel van een commit message met het issuenummer, gevolgd door een korte beschrijving op dezelfde regel:

```
#634 Nieuwe natuur afgeleid uit de landgebruikskaart
```

Visual Studio toont in de commitlijst alleen die eerste regel, dus daar moet de verwijzing staan en niet in de body. Hoort een commit bij geen enkel issue, dan begint de onderwerpregel gewoon met de beschrijving. Raakt hij meerdere issues, zet het belangrijkste nummer vooraan en de rest in de body.

Sluitende woorden als "Fixes #634" sluiten het issue automatisch zodra de commit in main belandt. Gebruik die alleen wanneer het issue daarmee echt af is.

## Bestandsvorm

Alle tekstbestanden staan in de werkkopie op CRLF en in git op LF; `.gitattributes` dwingt dat af, onafhankelijk van `core.autocrlf`. Dms-bestanden zijn UTF-8 zonder BOM en springen in met tabs (`.editorconfig`). Bewerk dms-bestanden in bytes of met `newline=''`, zodat een scriptbewerking de regeleindes niet omzet en geen BOM toevoegt. Controleer na een scriptbewerking `git diff --stat`: een diff van ongeveer twee keer het aantal regels van het bestand betekent dat de regeleindes zijn geraakt, en die hoort niet in een commit.

## Descr en Source

Een Descr zegt wat het item doet of betekent, in een zin; waar nodig waarom het er is, en bij een instelling wat de consequentie van de waarde is. Een verwijzing met hekje naar het issue waar de afweging staat blijft. De bron van een kental of een dataset staat in de property `Source`, met jaargang of leveringsdatum; een afleiding van een regel mag daar ook staan, een afleiding van een alinea staat in het issue.

Eruit blijven: meetuitkomsten en de datum ervan, de geschiedenis van wat er eerder stond, de weg waarlangs een fout is gevonden, lessen over GeoDMS (skill geodms-valkuilen), instructies aan de volgende lezer (skills) en versienummers of exitcodes. Vorm: een aaneengesloten tekst zonder witregels, inline waar dat kan, vervolgregels ingesprongen op de itemregel plus drie tabs. Richtpunt: parameters en attributen onder de 300 tekens, containers en sjablonen onder de 800.

## Meetharnassen

Een harnas dat een vraag uit een issue beantwoordt is tijdelijk en gaat weg zodra het issue dicht is; de meting staat dan in het issue. Wat blijft staat in een thematische container van `cfg/main/Diagnose.dms` (Waterberging, Natuur, Groen, Werken en zo verder) onder een naam die zegt wat er gemeten wordt, draait mee in `GenerateAll` of `GenerateBasisjaar` of zegt in zijn Descr dat het op aanvraag is, en heeft als controlewaarde een norm in `batch/ToetsOplevering.ps1`. Geen containers of bestanden met een issuenummer als naam.
