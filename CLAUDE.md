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

Geen persoonsnamen in Descr, Source of commentaar. Wie een bestand heeft aangeleverd, gemaild of een expert judgement heeft gegeven staat in de code als organisatie plus volgnummer: `PBL-3`, `Deltares-7`, `ObjectVision-1`, `WUR-5`. De koppeling van nummer naar persoon staat in een afgeschermde lijst buiten de repo (pbl-nl/model-RSopen#1); een nieuwe persoon krijgt het eerstvolgende nummer binnen de organisatie en komt eerst in die lijst. Wat wel blijft: auteurs van gepubliceerd werk met titel of DOI, de contactpersonen in de bestandsheaders en organisatienamen. Een gebruikersnaam in een pad telt ook als persoonsnaam.

## SourceData en BaseData

SourceData leest de bronnen in en koppelt ze aan de klassen. Een afleiding hoort in BaseData als zijn uitkomst een eigen kaart of tabel is, zoals een vergridding, een buffer of een afstandskaart; de afnemers lezen hem dan ook in BaseData. Een eigenschap van een ingelezen object, zoals de typering of een telling per pand, blijft bij dat object in SourceData, ook als hij ontkoppeld wordt weggeschreven naar `%LocalDataProjDir%/BaseData`. SourceData mag in een richting uit BaseData lezen. Een verwijzing die heen en weer gaat, van een object in SourceData naar een afleiding in BaseData en weer terug naar datzelfde object, hoort er niet in (#440).

## Meetharnassen

Een harnas dat een vraag uit een issue beantwoordt is tijdelijk en gaat weg zodra het issue dicht is; de meting staat dan in het issue. Wat blijft staat in een thematische container van `cfg/main/Diagnose.dms` (Waterberging, Natuur, Groen, Werken en zo verder) onder een naam die zegt wat er gemeten wordt, draait mee in `GenerateAll` of `GenerateBasisjaar` of zegt in zijn Descr dat het op aanvraag is, en heeft als controlewaarde een norm in de kolommen `norm_onder` en `norm_boven` van `Checks` of `ChecksBasisjaar`. Geen containers of bestanden met een issuenummer als naam.

## Takken

`main` is de stam van RSopen. Generiek werk komt op een korte eigen tak vanaf `main` en gaat terug naar `main`: rekenregels, het inlezen van een bron, indicatoren, Descr's, scripts en skills, alles wat in meer dan een project geldt. Een projecttak (`NL2120`, `dgwb-stad`, `dgwb-veenweide` en de andere) haalt `main` binnen wanneer hij het nodig heeft. Wat bij een project hoort blijft op de projecttak: de varianten en hun parameters, het studiegebied, het productieprofiel en de leveringen. Wordt op een projecttak iets generieks gebouwd, zet het dan in een eigen commit en breng die naar `main`.

`main` wijkt op vaste plekken af van de projecttakken: `VariantK.dms` heeft alleen de kolom van BAU, het productieprofiel staat op Standaard met alleen wonen en werken, de natuuroplegging staat standaard uit, het basisjaar-beheertype op Heuristiek, `BAG_WP5_rel_Ontkoppeld` op FALSE, de rootcontainer heet `RSopen`, `DiagCasus` en `Write_LastYear` staan op BAU, en `batch/RunAll.cmd` heeft een eigen `LocalDataProjDir`. Bij een merge van `main` in een projecttak houdt de projecttak op die plekken zijn eigen keuze. Een wijziging aan `VariantK.dms` op `main` botst daardoor vaak; breng die in de projecttak met de hand aan in de kolommen van zijn eigen varianten.

Een tak die van `NL2120` is afgesplitst en `main` nog nooit heeft binnengehaald, haalt eerst een keer `NL2120` binnen: daarin is `main` op 7 november 2026 opgenomen met deze afwijkingen opgelost. Daarna haalt hij `main` zelf. Komt daarbij de fingerprint-hash (#878) voor het eerst in de tak, hernoem dan eerst de ontkoppelde bestanden in zijn LocalData met `batch/OntkoppeldNaarHash.py <LocalData> --uitvoeren`, anders rekent het model alles opnieuw.
