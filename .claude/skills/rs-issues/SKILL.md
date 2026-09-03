---
name: rs-issues
description: Tekst schrijven die op GitHub terechtkomt in de openbare RSopen-repo; issues, comments, PR-beschrijvingen en commit messages. Regelt de stijlconventies, het verwijzen met hekje, wanneer je zelf plaatst en wanneer je eerst een concept toont, de lijst met openstaande punten onderaan, en wat er moet gebeuren voordat een issue dicht mag. Gebruik bij elk verzoek om een issue op te stellen, ergens op te reageren, een issue te sluiten of een commit message te schrijven.
---

# Tekst voor GitHub in RSopen

De repo ObjectVision/RSopen is openbaar en elke comment mailt direct alle betrokkenen bij Deltares, PBL en VU. Dat is niet terug te draaien. Daarom gelden hier strengere regels dan voor gewone documentatie.

## Wat je zelf plaatst en wat niet

Zegt de gebruiker "plaats", "maak", "sluit" of iets anders in de gebiedende wijs, dan is dat de toestemming en voer je het uit. Dat geldt voor een nieuw issue, voor een comment op een bestaand issue, voor het sluiten van een issue en voor een PR-beschrijving. Meld daarna het nummer of de link. Een concept aanleveren en op akkoord wachten is dan niet wat er gevraagd is, ook niet als extra zorgvuldigheid bedoeld.

Zonder zo'n opdracht lever je de tekst eerst als concept aan, in de ik-vorm, en plaats je hem pas na akkoord. Dat is de stand bij "wat vind je hiervan", bij een voorstel dat je zelf doet, en bij alles waar de gebruiker nog geen handeling heeft genoemd.

Instemming met een plan blijft geen instemming met publiceren. Een akkoord op een aanpak, op "de vragen terugleggen" of op een conclusie is dus geen opdracht om te plaatsen. Daarvoor is een opdracht nodig die de handeling zelf noemt.

Schrijf het concept in de ik-vorm, namens de gebruiker. Niet in de wij-vorm en niet namens Object Vision als collectief. Geen verwijzing naar Claude of co-authorship, ook niet in commit messages.

## Stijl

Geen echte persoonsnamen. Verwijs naar de organisatie: Deltares, PBL, Object Vision, VU. Dus "vraag vanuit Deltares" en niet de naam van de betreffende onderzoeker. Dit geldt in titels, bodies en comments, en ook als de naam elders in de repo of in de chat staat.

Geen vetgedrukte tekst in de lopende tekst. Vet is alleen voor kopjes, niet voor woorden of zinsdelen binnen alinea's, opsommingen of tabelcellen.

Geen gedachtenstreepjes, dus geen em dash of en dash als leesteken. Herschrijf de zin, of gebruik een komma, een dubbele punt of een punt. Deze regel geldt ook buiten issues: in commit messages, documentatie en antwoorden in de chat.

## Verwijzen met hekje

Schrijf altijd `#634`, nooit "issue 634" of alleen "634". GitHub herkent alleen de vorm met hekje. Zonder hekje verschijnt de commit niet in de tijdlijn van het issue en moet de koppeling met de hand gelegd worden.

In een commit message begint de onderwerpregel met het issuenummer, gevolgd door de beschrijving op dezelfde regel. Visual Studio toont in de commitlijst alleen die eerste regel, dus daar moet de verwijzing staan.

```
#620 Kansrijke woningbouwlocaties opgenomen in de trede voor wonen

De trede leest nu BBGPlusKansrijkWoningbouw in plaats van BBG, zodat de
kansrijke locaties meetellen bij de afweging.
```

Hoort een commit bij geen enkel issue, dan begint de onderwerpregel gewoon met de beschrijving. Raakt hij meerdere issues, zet het belangrijkste nummer vooraan en noem de rest in de body.

Sluitende woorden als `Fixes #634` sluiten het issue automatisch zodra de commit in main belandt. Gebruik die alleen wanneer het issue daarmee echt af is.

Is de commit al gemaakt maar nog niet gepusht, dan is `git commit --amend` de fix.

## Voor je commit

In deze werkkopie draaien regelmatig meerdere sessies tegelijk, niet in aparte worktrees. Commit daarom alleen je eigen bestanden met een expliciete `git add`, nooit `git add -A` of `git commit -a`. Controleer `git status` vlak voor de commit, niet alleen aan het begin van het werk.

Een expliciete `git add` is niet genoeg: een bestand waar jij aan hebt gezeten kan ondertussen ook door een andere sessie zijn aangepast. Loop daarom voor elk bestand dat je stageert de diff langs en stel vast dat elke regel van jou is. Zit er werk van iemand anders in hetzelfde bestand, stageer dan alleen je eigen hunks. Interactief `git add -p` kan hier niet, dus via een deelpatch:

```
git diff <bestand> > /tmp/vol.patch
grep -n "^@@" /tmp/vol.patch          # welke hunk is van jou
sed -n '1,4p;<start>,<eind>p' /tmp/vol.patch > /tmp/mijn.patch
git apply --cached /tmp/mijn.patch
git diff --cached <bestand>           # controleer dat er niets van een ander in zit
```

Controleer na de commit met `git status` dat het werk van de andere sessie nog als working copy overeind staat.

Belangrijker nog: de index is gedeeld, net als de bestanden. `git add` gevolgd door `git commit` is dus niet atomair. Staat er tussen die twee opdrachten iets van een ander gestaged, dan pakt jouw commit dat mee, want een kale `git commit` neemt de hele index. Commit daarom met een expliciete padlijst achter twee streepjes:

```
git commit -- cfg/main/MijnBestand.dms cfg/main.dms
```

Die vorm commit alleen de genoemde paden en laat de rest van de index met rust. Gebeurd op 2026-08-31, twee keer op een avond en in beide richtingen: een commit voor #724 nam drie gestagede bestanden van de #705-sessie mee, en die sessie zag daarna "nothing to commit" en dacht even dat haar werk verdampt was. Terug te vinden via de reflog, en met `git reset --soft HEAD~1` te herstellen zolang er niet gepusht is, maar dat is een schrik die je niemand gunt.

Controleer dus voor je commit niet alleen `git status` maar ook of de index leeg is van andermans werk.

### Maar de padvorm negeert je zorgvuldige stagen

De padvorm lost het ene probleem op en maakt het andere erger, en die twee kun je niet tegelijk met deze opdracht oplossen. `git commit -- <pad>` commit de WERKKOPIE van dat pad en negeert wat er voor dat pad gestaged staat; dat is de betekenis van `--only`, de standaard zodra je paden meegeeft. Heb je hierboven met een deelpatch alleen je eigen hunks gestaged, dan gooit de padvorm dat werk weg en commit hij het hele bestand, inclusief de ongecommitte wijzigingen van de andere sessie.

Gebeurd op 2026-09-01 in `Zeef_T.dms`: de #586-commit nam zo het ongecommitte #682-werk mee, waarna de #682-sessie vanaf een werkkopie zonder #586 committe en de hele #586-wijziging terugdraaide.

De vuistregel die daaruit volgt:

- ben jij de enige die aan die bestanden heeft gezeten, gebruik dan de padvorm; die beschermt tegen andermans werk in de gedeelde index
- zit er werk van een ander in hetzelfde bestand, gebruik dan geen van beide vormen, maar bouw de commit via een tijdelijke index, zodat noch de werkkopie noch de gedeelde index wordt aangeraakt

```bash
OLD=$(git rev-parse HEAD)          # een keer bepalen, hieronder drie keer gebruiken
git diff $OLD -- <bestand> > /tmp/alles.patch
grep -n "^@@" /tmp/alles.patch     # welke hunks zijn van jou
sed -n '1,4p;<start>,<eind>p' /tmp/alles.patch > /tmp/mijn.patch
export GIT_INDEX_FILE=/tmp/idx
git read-tree $OLD
git apply --cached /tmp/mijn.patch
TREE=$(git write-tree)
unset GIT_INDEX_FILE
NEW=$(git commit-tree $TREE -p $OLD -F /tmp/bericht.txt)
git update-ref refs/heads/<branch> $NEW $OLD
git reset -- <bestand>             # index weer op HEAD, werkkopie blijft
```

Twee dingen die hierbij misgaan.

Bepaal `$OLD` een keer en gebruik diezelfde waarde voor `read-tree`, voor `-p` en voor de guard. Leest de tweede aanroep `HEAD` opnieuw uit, dan kan er ondertussen een commit van een andere sessie tussen zijn gekomen en hangt jouw boom aan een nieuwere ouder dan zijn eigen basis. Alles wat daartussen zat verdwijnt dan zonder conflict en zonder waarschuwing, want een boom is compleet en zegt niets over zijn herkomst. De `$OLD`-guard op `update-ref` vangt dat niet, want die kijkt alleen of de ref nog op `$OLD` staat en dat klopt dan.

Sla die laatste `git reset` niet over, ook niet als je alle bestanden zelf hebt geschreven. Commit je via een eigen `GIT_INDEX_FILE`, dan blijft de gedeelde index staan waar hij stond, terwijl HEAD vooruit gaat. `git status` toont daarna elk gewijzigd bestand als `MM`, en `git diff --cached` geeft precies de inverse van wat je zojuist hebt gecommit: min zesendertig regels waar je er zesendertig hebt toegevoegd. Dat leest als werk van een ander dat op verdwijnen staat, terwijl er niets aan de hand is. Gemeten op 2026-09-02, na twee commits met een tijdelijke index: elf bestanden op `MM`, terwijl `git diff HEAD` leeg was voor al die elf. Een kale `git reset` zonder paden zet de index terug op HEAD en laat de werkkopie met rust; dat is de opruiming.

Toets het verschil dus altijd tegen HEAD en niet tegen de index. `git diff HEAD --stat` zegt wat er werkelijk open staat, `git status` niet.

Controleer achteraf altijd met `git show --stat <commit>`. Staat er een bestand in dat jij niet hebt aangeraakt, dan hing je boom aan een verouderde basis of heeft de padvorm de werkkopie gepakt. Dat is de goedkoopste kanarie voor allebei de fouten.

Let op de blinde vlek bij untracked bestanden: `git diff` geeft daar niets, en een lege diff leest als schoon terwijl het hele bestand meegaat bij `git add`. In een gedeeld diagnosebestand kan dan werk van een andere sessie in je commit belanden; dat is op 2026-08-28 gebeurd met de container D703 in Diagnose667.dms. Bekijk voor een nieuw bestand dus altijd de volledige inhoud, of `git diff --cached` na het stagen, voordat je commit.

Commit of push alleen wanneer daarom gevraagd is.

## Een issue sluiten

"Dit issue mag dicht" betekent drie handelingen, in deze volgorde:

1. Plaats een afrondende comment: wat er is gedaan, met welke uitkomst, en wat er eventueel blijft liggen. Iemand die het issue later opzoekt moet zonder de code te openen begrijpen waarom het dicht kon.
2. Commit de bijbehorende wijzigingen, met het issuenummer vooraan in de onderwerpregel.
3. Sluit het issue.

Blijkt bij het afronden dat het issue nog niet af is, sluit het dan niet. Zeg wat er nog open staat en laat de keuze bij de gebruiker.

## Een goed issue

Noem het pad in de config waar het over gaat, met bestandsnaam en regelnummer als je die hebt. Noem het gemeten getal en waartegen je het afzet. Scheid de waarneming van de interpretatie: wat je gemeten hebt is een feit, waarom het zo is is een hypothese totdat het aangetoond is. Zeg expliciet wat je niet getoetst hebt.

## Openstaande punten onderaan, in bullets

### Toets eerst of de vraag nodig is

Doe dit voordat je de bullets opschrijft, niet erna. Elke vraag mailt alle betrokkenen en legt werk bij een ander neer, en een vraag die al beantwoord is kost de ontvanger meer tijd dan hij jou bespaart. Loop per bullet deze drie langs en schrap hem zodra er een raak is.

- staat het antwoord al ergens? Zoek ook in gesloten issues, want dat is hier juist de plek waar dingen zijn vastgelegd. Elk issue dat je in je eigen tekst noemt open je met `gh issue view <nummer> --comments`; dat is het minimum, want een vraag stellen over een issue dat je aanhaalt zonder het te lezen is niet uit te leggen.
- kun je hem zelf beantwoorden uit de configuratie of met een meting? Dan is het geen vraag maar werk dat je nog niet gedaan hebt.
- klopt de premisse? Een vraag in de vorm "omdat het model X niet doet" is pas een vraag als je hebt vastgesteld dat het model X inderdaad niet doet. Doe die vaststelling in de code en niet uit je hoofd.

Blijft er een vraag over, zet er dan bij wat je al hebt uitgesloten, zodat de ander niet opnieuw begint.

Gebeurd bij #763 op 3 september 2026. Ik plaatste drie vragen aan Deltares over de kentallen voor de kostenopslag per bouwwijze. Twee waren beantwoord in #505, dat gesloten is en waarin staat dat bijlage E al is overgenomen en dat er niets geleverd hoeft te worden. De derde rustte op de aanname dat het model aangepast bouwen niet beprijst, terwijl Bodemdalingkosten_T de ophoogdikte afleidt uit de schadevrije diepte van de gekozen bouwwijze en die post in het exploitatiesaldo zit. Een vierde punt stond in de code: BouwwijzeInput/Toegestaan zet alles op FALSE waar Stand/OP_rel leeg is. Alle vier hadden weg gekund, en de comment is achteraf aangepast.

Dit patroon herhaalt zich. Vraagt de gebruiker of de vragen nodig zijn, dan zijn ze dat vrijwel nooit; stel die vraag dus zelf, voordat je plaatst.

### De vorm

Blijft er na een issue of een comment iets openstaan, dan sluit je af met een kopje met de openstaande acties en vragen, als bullets. Niet verspreid door de lopende tekst, want dan moet de lezer zelf gaan turven wat er nu eigenlijk moet gebeuren.

Groepeer naar de partij die aan zet is, met die partij in het kopje en de bullets eronder zonder voorvoegsel. Zijn alle vragen voor dezelfde partij, dan is het één kopje. Formuleer elke bullet zo dat hij met ja, nee of een getal te beantwoorden is; "hier moet nog naar gekeken worden" is geen actie.

```
## Openstaande vragen Deltares

- welke restschadefactor geldt voor een opgehoogde woning onder de ontwerpdiepte?
- werkt die factor anders op inboedel dan op opstal?
- kent SSM2017 al functienummers voor aangepaste bebouwing?
```

Voeg zelf geen @-vermelding en geen persoonsnaam toe, ook niet om iemand te attenderen: het kopje noemt de organisatie, en wie er precies wordt aangesproken bepaalt de gebruiker bij het plaatsen.

In NL2120 is Deltares de tegenpartij. PBL zit niet in dit project, dus adresseer daar niets aan tenzij de gebruiker dat zelf zegt.

Staat er niets open, laat het kopje dan weg. Een lege lijst suggereert dat er nog iets komt.
