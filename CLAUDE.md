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

Zet de verwijzing in de eerste regel van de body van de commit message, niet in de onderwerpregel. Die blijft een korte beschrijving van de wijziging zelf.

Sluitende woorden als "Fixes #634" sluiten het issue automatisch zodra de commit in main belandt. Gebruik die alleen wanneer het issue daarmee echt af is.
