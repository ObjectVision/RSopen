---
name: rs-issues
description: Tekst schrijven die op GitHub terechtkomt in de openbare RSopen-repo; issues, comments, PR-beschrijvingen en commit messages. Regelt de stijlconventies, het verwijzen met hekje en de afspraak dat een concept wordt aangeleverd in plaats van zelf geplaatst. Gebruik bij elk verzoek om een issue op te stellen, ergens op te reageren of een commit message te schrijven.
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

Commit of push alleen wanneer daarom gevraagd is.

## Een goed issue

Noem het pad in de config waar het over gaat, met bestandsnaam en regelnummer als je die hebt. Noem het gemeten getal en waartegen je het afzet. Scheid de waarneming van de interpretatie: wat je gemeten hebt is een feit, waarom het zo is is een hypothese totdat het aangetoond is. Zeg expliciet wat je niet getoetst hebt.
