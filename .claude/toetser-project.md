# Wat de toetser in RSopen extra nagaat

De toetser (de gedeelde agent `toetser`, via de skill `rapport-voorleggen`) leest dit bestand naast zijn vaste punten. Het zegt wat in RSopen extra telt voordat een rapport of concept wordt voorgelegd. De punten komen uit de bijsturing in de sessies tussen juni en november 2026; een correctie die de toetser toch mist, komt hier bij.

- De kaart. Zijn de kaarten van elk zichtjaar per regio bekeken, ingezoomd? Let op ringen, banden, losse clusters ver van een kern, snippers en sprongen tussen jaren. Een proefrun die alleen het eerste zichtjaar rekent, toetst niets wat over de jaren heen doorwerkt.
- Bekende plekken. Is de uitkomst plausibel waar iedereen het kan zien? Een park als het Vondelpark of een universiteitscampus wordt niet volgebouwd, en het IJ is geen bebouwd gebied.
- Het modelmechanisme. Klopt een verklaring met wat de configuratie doet? Zoek de regel op in `cfg/` voordat je een oorzaak aanneemt. GeoDMS heeft geen rekencache meer; een verklaring die daarop leunt, klopt niet.
- De indeling. Volgt nieuwe code de bestaande boom en de afspraak over SourceData en BaseData in `CLAUDE.md`? Staat er een schakelaar bij een verbetering, een kaal getal buiten `ModelParameters`, of een nieuwe eigen naam waar al een term bestond?
- De vergelijking. Is het enige verschil tussen twee runs het bedoelde verschil, op dezelfde codestand? Is de controle op ontkoppelde bestanden gedaan als een weggeschreven bestand geraakt kan zijn (skill `rs-fingerprints`)?
- Het rekenwerk. Is er niet zwaarder gedraaid dan de vraag vroeg, bijvoorbeeld een landelijke run waar een provincie of een zichtjaar volstond?
- SourceData. Is er niets geschreven in `%SourceDataDir%`?
- Vragen aan Deltares of PBL. Staat het antwoord al in een issue, een bijlage, een rapport of de code (skill `rs-issues`, sectie Openstaande punten)?
- Tekst voor GitHub. Volgt hij `CLAUDE.md` van de repo en de skill `rs-issues`?
