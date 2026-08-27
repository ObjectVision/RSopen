---
name: rs-issues
description: Tekst schrijven die op GitHub terechtkomt in de openbare RSopen-repo; issues, comments, PR-beschrijvingen en commit messages. Regelt de stijlconventies, het verwijzen met hekje, de afspraak dat een concept wordt aangeleverd in plaats van zelf geplaatst, de lijst met openstaande punten onderaan, en wat er moet gebeuren voordat een issue dicht mag. Gebruik bij elk verzoek om een issue op te stellen, ergens op te reageren, een issue te sluiten of een commit message te schrijven.
---

# Tekst voor GitHub in RSopen

De repo ObjectVision/RSopen is openbaar en elke comment mailt direct alle betrokkenen bij Deltares, PBL en VU. Dat is niet terug te draaien. Daarom gelden hier strengere regels dan voor gewone documentatie.

## Niet zelf plaatsen

Plaats nooit zelf een issue of comment op GitHub. Lever de tekst aan als concept in een bestand, dan wordt hij zelf geplaatst na lezing.

Instemming met een plan is geen instemming met publiceren. Ook een eerder akkoord op "de vragen terugleggen" is dat niet. Vraag apart om toestemming, of lever gewoon het concept. Alleen op een expliciet verzoek in de trant van "plaats de issues zelf maar" mag je direct plaatsen.

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

Blijft er na een issue of een comment iets openstaan, dan sluit je af met een kopje met de openstaande acties en vragen, als bullets. Niet verspreid door de lopende tekst, want dan moet de lezer zelf gaan turven wat er nu eigenlijk moet gebeuren.

Zet per bullet wie het kan oppakken, zodat de juiste mensen aangestuurd kunnen worden. Splits daarbij naar partij: een vraag die alleen Deltares, PBL of VU kan beantwoorden is iets anders dan een beslissing die bij Object Vision ligt of een stuk werk in de configuratie. Formuleer elke bullet zo dat hij met ja, nee of een getal te beantwoorden is; "hier moet nog naar gekeken worden" is geen actie.

```
## Openstaande punten

- Deltares: welke restschadefactor geldt voor een opgehoogde woning onder de ontwerpdiepte?
- Deltares: werkt die factor anders op inboedel dan op opstal?
- Object Vision: schakelaar blijft op FALSE tot die factoren er zijn, akkoord?
- Configuratie: het weggeboekte bedrag als tweede indicator publiceren.
```

Staat er niets open, laat het kopje dan weg. Een lege lijst suggereert dat er nog iets komt.
