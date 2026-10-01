"""De controle die voor een productierun draait: mag deze run beginnen.

Gebruik:
    python Preflight.py [opties]

Opties:
    --cfg <pad>          de configuratie; default cfg/main.dms naast dit script
    --exe <pad>          GeoDmsRun.exe; default de versie uit batch/RunAll.cmd
    --scenario <naam>    scenario voor de resolutieronde; default WLO_hoog
    --variant <naam>     variant voor de resolutieronde; default BAU
    --boom               voeg laag 3 toe (de resolutieronde). Standaard uit; zie de waarschuwing hieronder.
    --uit <map>          waar het rapport komt; default <LocalData>/Preflight

Drie lagen, van goedkoop naar duur, elk met een eigen exitcode-bijdrage. Het script stopt niet bij de
eerste fout maar draait alle lagen, zodat een run in een keer alles te horen krijgt wat er mis is, en
geeft exit 1 zodra een laag faalt.

1. Profiel: staan de sleutelparameters op de stand die bij deze projectlijn hoort (ModelParameters/
   Productieprofiel). De tabel en de norm staan in cfg/main/Preflight.dms; dit script vraagt eerst de
   csv op en daarna de telling, zodat de csv er ook staat wanneer de telling de run afbreekt.
2. Invoer: staan de bestanden er die pas laat in de run gelezen worden? De ontkoppelde basedata (een
   representatief bestand per stap, met de stap die het maakt), de plancapaciteitsgrids per zichtjaar
   en de claim-CSV van het eerste zichtjaar. Zonder deze laag stranden die pas na een uur rekenen, en
   een ontbrekend mmd meldt zich bovendien als een onbekende naam en niet als een ontbrekend bestand.
3. Boom: lost elk productie-item op. GeoDmsRun lost eerst alle namen op en begint daarna pas te
   rekenen; dit script stopt het proces zodra de eerste Updating-regel verschijnt en rapporteert de
   [E]-regels uit de resolutieronde. Dat vangt een verwijzing naar een verdwenen item, zoals bij #759,
   voordat de run begint. Deze laag draait in een wegwerpkopie van cfg met een eigen LocalData, nooit
   op die van de werkkopie: het rekenen begint in dezelfde seconde als de laatste resolutieregel, en
   GeoDMS leegt het bestand van een schrijvend item aan het begin van dat item. Op de gedeelde
   LocalData zou een halfgeschreven tif van een eerdere run achterblijven.

Wat laag 3 NIET vangt: een meta-expressie instantieert alleen de tak die bij de huidige schakelaars
hoort, en een item in een Template bestaat pas na instantiatie. Een boomcontrole over alle takken
vraagt om UpdateMetaInfo in de Python-binding van GeoDMS; aangevraagd in ObjectVision/GeoDMS#1279.
Zolang die er niet is, dekt laag 3 de gekozen takken van het actieve profiel.

WAAROM LAAG 3 STANDAARD UIT STAAT. Hij vindt echte fouten: op 22 september 2026 kwamen ObjectVision/
RSopen#838 (een toets die twee varianten bij naam noemde) en een pad zonder leidende slash in de
plancapaciteitsoplegging er uit, allebei fouten die een productierun zouden hebben afgebroken. Maar de
wegwerpkopie heeft een lege LocalData, en daar levert elke store die zijn kolommen uit een bestand
haalt een "Unknown identifier <kolomnaam>" op in plaats van een bestandsfout. Die twee zijn uit de
melding niet te onderscheiden. Na het meekopieren van de mmd-stores en het filteren van twee bekende
categorieen bleef er een staart over die per ronde een nieuwe naam opleverde, elke keer met exit 0 op
de echte configuratie. De signaal-ruisverhouding is daarmee omgeslagen.

Zet hem aan met --boom wanneer je gericht naar naamfouten zoekt, bijvoorbeeld na een merge of na het
verwijderen van een item, en toets elke melding daarna los op de echte configuratie voordat je hem
gelooft. Structureel wordt dit pas opgelost door UpdateMetaInfo in de Python-binding van GeoDMS
(ObjectVision/GeoDMS#1279): dan hoeft er geen bestand meer te bestaan om een naam te kunnen opzoeken.

Uitvoer: <uit>/preflight.csv met laag, toets, oordeel en melding, en hetzelfde op het scherm.
Zie pbl-nl/model-RSopen#53 en ObjectVision/RSopen#833; wat laag 3 als eerste vond staat in
ObjectVision/RSopen#838.
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Laag 3 is een naamcontrole. In de wegwerpkopie is de LocalData leeg, dus elk item dat een tif of een
# mmd van een eerdere stap terugleest meldt daar een bestandsfout. Die zegt niets over de code en hoort
# bij laag 2; alleen de meldingen hieronder tellen als fout van laag 3.
BESTANDSFOUT = ("TIFFOpen Error", "cannot open dataset", "No such file or directory", "Cannot open",
                "cannot be opened", "Failure(4)")

# Namen die een operator pas bij het rekenen aan zijn unit hangt. De resolutieronde kijkt ervoor en
# meldt ze als onbekend, terwijl ze in een echte run gewoon bestaan: de allocatielogs van de
# NL2120-productierun van 29 augustus 2026 (run2120/*allocatie-BAU-Y20*.log) bevatten geen enkele
# foutregel, terwijl elke iteratie deze items aanroept. Districts komt van district_8 in
# Templates/Allocatie/Iter_T/Iter_Allocatie.dms, waar het de clusters van aaneengesloten cellen geeft.
# Voeg een naam hier alleen toe nadat je hebt vastgesteld dat een geslaagde run hem wel oplost.
OPERATOR_SUBITEM = ("Unknown identifier 'Districts'",)

# Een representatief bestand per basedata-stap, met de stap die het maakt. Overgenomen uit de
# eis-lijst van batch/Run2120.ps1 (ObjectVision/RSopen#816): zeg vooraf welk ontkoppeld bestand
# ontbreekt, in plaats van na een uur rekenen om te vallen op "Unknown identifier". De lijst is een
# ondergrens en geen inventaris. Paden zijn relatief aan de LocalData van deze werkkopie.
BASEDATA = [
    ("BaseData/Vastgoed/VolledigeTabel_*/WP5/*.mmd",         "WP5-pandtypering",        "/WriteBaseData/Generate_Run1"),
    ("BaseData/Grondgebruik/BBG/BBG*_25m_Modus_*.tif",       "BBG-vergridding",         "/WriteBaseData/Generate_Run2"),
    ("BaseData/Vastgoed/Verwervingskosten_Woningen_*.tif",   "verwervingskosten",       "/WriteBaseData/Generate_Run2"),
    ("BaseData/StandBasisjaar/Wonen/*.tif",                  "stand basisjaar",         "/WriteBaseData/Generate_Run3"),
    ("BaseData/Vastgoed/WP2xVSSH_Proxy/*",                   "woningsubsector-proxies", "/WriteBaseData/Generate_Run3"),
    ("BaseData/Vastgoed/Sloopkosten_Woningen_*.tif",         "sloopkosten",             "/WriteBaseData/Generate_Run3"),
    ("BaseData/Suitabilities/Werken_raw_*.tif",              "werken-geschiktheid",     "/WriteBaseData/Generate_Run3"),
]

PROFIEL_ITEMS = ["/Preflight/Profiel/Schrijf", "/Preflight/Profiel/Afwijkingen"]
INVOER_ITEMS = ["/Preflight/Invoer/Plancapaciteit", "/Preflight/Invoer/Claims"]
# De items die RunAll.cmd, RunVariantData.cmd en RunZichtjaren.cmd opvragen, in die volgorde.
BOOM_ITEMS = [
    "/WriteBaseData/Generate_Run1",
    "/WriteBaseData/Generate_Run2",
    "/WriteVariantData/per_Variant/@VARIANT@/Generate_Run1",
    "/WriteVariantData/per_Variant/@VARIANT@/Generate_Run2",
    "/Allocatie/@CASUS@/Zichtjaren/@ZICHTJAAR@/Impl/Generate",
    "/Indicatoren/@CASUS@/Zichtjaren/Export/Generate_Indicatoren",
]


def projdir() -> Path:
    return Path(__file__).resolve().parent.parent


def localdata() -> Path:
    """GeoDMS leidt LocalDataProjDir af uit C:/LocalData plus de mapnaam boven cfg."""
    return Path("C:/LocalData") / projdir().name


def exe_uit_runall() -> str:
    """De GeoDMS-versie die RunAll.cmd zet, zodat de preflight niet op een andere versie toetst."""
    tekst = (projdir() / "batch" / "RunAll.cmd").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^set geodmsversion=(\S+)", tekst, re.M)
    versie = m.group(1) if m else "GeoDms20.17.0.m"
    return rf"C:\Program Files\ObjectVision\{versie}\GeoDmsRun.exe"


def eerste_zichtjaar(cfg: Path) -> str:
    """Model_FirstZichtjaar uit ModelParameters.dms; de configuratie blijft de bron, niet dit script."""
    tekst = (cfg.parent / "main" / "ModelParameters.dms").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Model_FirstZichtjaar\s*:=\s*(\d{4})", tekst)
    return f"Y{m.group(1)}" if m else "Y2030"


def draai(exe: str, cfg: Path, items: list[str], log: Path, stop_bij_updating: bool = False, max_seconden: int = 900) -> tuple[int, list[str]]:
    """Roep GeoDmsRun aan en geef de exitcode plus de foutregels terug.

    Met stop_bij_updating wordt het proces gestopt zodra de eerste Updating-regel in het log staat: dan
    is de resolutieronde klaar en begint het rekenen. Het log wordt met gedeelde toegang gelezen, want
    GeoDmsRun houdt het tijdens de run open voor schrijven.
    """
    log.parent.mkdir(parents=True, exist_ok=True)
    log.unlink(missing_ok=True)
    p = subprocess.Popen([exe, f"/L{log}", "/S1", "/S2", "/S3", str(cfg), *items],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if stop_bij_updating:
        begin = time.time()
        while p.poll() is None and time.time() - begin < max_seconden:
            time.sleep(0.2)
            try:
                with open(log, "r", encoding="utf-8", errors="replace") as f:
                    if "Updating::" in f.read():
                        p.terminate()
                        break
            except OSError:
                continue
    try:
        p.wait(timeout=max_seconden)
    except subprocess.TimeoutExpired:
        p.kill()
    fouten = []
    if log.exists():
        with open(log, "r", encoding="utf-8", errors="replace") as f:
            for regel in f:
                if "[E]" in regel:
                    fouten.append(regel.split("[progress]")[-1].split("[other]")[-1].strip())
    return (p.returncode if p.returncode is not None else 1), fouten


def kort(fouten: list[str], n: int = 3) -> str:
    """De eerste paar foutregels, zonder de herhalingen die GeoDMS per contextniveau toevoegt."""
    uniek = []
    for f in fouten:
        if f.startswith("Context:") or f.startswith("1. ") or f.startswith("ErrorLevel"):
            continue
        if f not in uniek:
            uniek.append(f)
    return " | ".join(uniek[:n])


# De schakelaars die een tussenresultaat uit een ontkoppeld bestand lezen in plaats van het te rekenen.
# In de wegwerpkopie gaan ze uit; zie wegwerpkopie() voor waarom.
ONTKOPPEL_SCHAKELAARS = ["BaseDataOntkoppeld", "VariantDataOntkoppeld", "StandAllocatieOntkoppeld",
                         "IndicatorenOntkoppeld", "OpbrengstdervingOntkoppeld", "BAG_WP5_rel_Ontkoppeld"]


def wegwerpkopie(cfg: Path) -> tuple[Path, Path]:
    """Kopieer cfg naar een map met een eigen naam, zodat GeoDMS een eigen LocalData afleidt.

    GeoDmsRun negeert de omgevingsvariabele LocalDataProjDir en leidt het pad af uit C:/LocalData plus
    de mapnaam boven cfg. Een eigen LocalData vraagt dus om een eigen mapnaam, niet om een variabele.
    De kopie is ongeveer 5 MB en gaat na afloop weg; de brondata staat buiten cfg en wordt niet geraakt.

    In de kopie gaan de ontkoppel-schakelaars uit. Die LocalData is leeg, en een unit die haar kolommen
    uit een mmd-storage haalt (AfleidingPandType/Results) heeft zonder dat bestand geen kolom WP5_rel;
    de resolutie meldt dan een onbekende naam voor een bestand dat ontbreekt, niet voor code die fout is.
    Met de schakelaars uit kiest elke meta-expressie de tak die rekent, en dat is de tak die in de
    configuratie staat en dus de tak die deze laag hoort te toetsen. Of de ontkoppelde bestanden er zijn
    is een vraag voor laag 2 en voor Templates/DecoupledFile_T, niet voor een naamcontrole.
    """
    doel = cfg.parent.parent.parent / f"{projdir().name}_Preflight"
    if doel.exists():
        shutil.rmtree(doel, ignore_errors=True)
    shutil.copytree(cfg.parent, doel / "cfg")
    # De mmd-stores meenemen. Een mmd levert zijn kolommen uit de dictionary in het bestand, dus zonder
    # die stores meldt elke lezer een onbekende naam in plaats van een ontbrekend bestand, en dat is in
    # een naamcontrole niet van een echte fout te onderscheiden. Het zijn mappen van samen ongeveer 50 MB
    # (de WP5-pandtypering en de woningsubsector-proxies), dus dat is te doen; de tifs blijven weg, want
    # die melden zich netjes als bestandsfout en worden hierboven gefilterd.
    bron = localdata()
    doel_ld = Path("C:/LocalData") / doel.name
    for mmd in bron.rglob("*.mmd"):
        naar = doel_ld / mmd.relative_to(bron)
        naar.parent.mkdir(parents=True, exist_ok=True)
        if mmd.is_dir():
            shutil.copytree(mmd, naar, dirs_exist_ok=True)
        else:
            shutil.copy2(mmd, naar)
        xml = mmd.with_suffix(".xml")
        if xml.exists():
            shutil.copy2(xml, naar.with_suffix(".xml"))

    mp = doel / "cfg" / "main" / "ModelParameters.dms"
    tekst = mp.read_bytes().decode("utf-8")
    for naam in ONTKOPPEL_SCHAKELAARS:
        # De regel in zijn geheel vervangen: sommige lezen hun waarde uit de omgeving, en een
        # omgevingsvariabele zou de vaste waarden hieronder niet raken.
        # Non-greedy tot de eerste ", Descr" op dezelfde regel: de env-gestuurde schakelaars hebben
        # komma's in hun expressie, en de Descr loopt door op vervolgregels die moeten blijven staan.
        tekst, n = re.subn(rf"(?m)^(\s*parameter<[Bb]ool>\s+{naam}\s+):=.*?(,\s*Descr)",
                           r"\g<1>:= FALSE\g<2>", tekst)
        if n != 1:
            raise SystemExit(f"schakelaar {naam} niet eenduidig gevonden in {mp}; pas ONTKOPPEL_SCHAKELAARS aan")
    mp.write_bytes(tekst.encode("utf-8"))
    return doel / "cfg" / cfg.name, doel


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cfg", default=str(projdir() / "cfg" / "main.dms"))
    ap.add_argument("--exe")
    ap.add_argument("--scenario", default="WLO_hoog")
    ap.add_argument("--variant", default="BAU")
    ap.add_argument("--boom", action="store_true")
    ap.add_argument("--uit")
    a = ap.parse_args(argv)

    cfg = Path(a.cfg)
    exe = a.exe or exe_uit_runall()
    uit = Path(a.uit) if a.uit else localdata() / "Preflight"
    logs = uit / "logs"
    if not Path(exe).exists():
        print(f"GeoDmsRun niet gevonden: {exe}", file=sys.stderr)
        return 2

    casus = f"{a.scenario}_{a.variant}"
    vervang = {"@VARIANT@": a.variant, "@CASUS@": casus, "@ZICHTJAAR@": eerste_zichtjaar(cfg)}
    print(f"configuratie : {cfg}\nGeoDmsRun    : {exe}\ncasus        : {casus}\nrapport      : {uit / 'preflight.csv'}\n")

    regels: list[dict[str, str]] = []

    def toets(laag: str, naam: str, items: list[str], cfg_override: Path | None = None,
              alleen_naamfouten: bool = False, **kw) -> None:
        t = time.time()
        code, fouten = draai(exe, cfg_override or cfg, items, logs / f"{naam}.log", **kw)
        genegeerd = 0
        if alleen_naamfouten:
            # Niet de exitcode maar de gefilterde foutenlijst geeft hier het oordeel: de exitcode is 1
            # zodra er een bestand ontbreekt, en dat is in een lege LocalData de normale toestand.
            schoon = [f for f in fouten if not any(b in f for b in BESTANDSFOUT + OPERATOR_SUBITEM)]
            genegeerd = len(fouten) - len(schoon)
            fouten, code = schoon, (1 if schoon else 0)
        oordeel = "PASS" if code == 0 else "FAIL"
        melding = "" if code == 0 else kort(fouten)
        staart = f", {genegeerd} bekende meldingen genegeerd" if genegeerd else ""
        regels.append({"laag": laag, "toets": naam, "oordeel": oordeel, "seconden": f"{time.time() - t:.1f}", "melding": melding})
        print(f"[{oordeel}] {laag}/{naam}  ({time.time() - t:.1f} s{staart})" + (f"\n       {melding}" if melding else ""))

    toets("1_profiel", "sleutelparameters", PROFIEL_ITEMS)

    ontbreekt = [(o, stap) for patroon, o, stap in BASEDATA if not list(localdata().glob(patroon))]
    t = time.time()
    melding = "; ".join(f"{o} ontbreekt, maak met {stap}" for o, stap in ontbreekt)
    regels.append({"laag": "2_invoer", "toets": "basedata", "oordeel": "FAIL" if ontbreekt else "PASS",
                   "seconden": f"{time.time() - t:.1f}", "melding": melding})
    print(f"[{'FAIL' if ontbreekt else 'PASS'}] 2_invoer/basedata" + (f"\n       {melding}" if melding else ""))

    for item in INVOER_ITEMS:
        toets("2_invoer", item.rsplit("/", 1)[-1].lower(), [item])
    if a.boom:
        items = list(BOOM_ITEMS)
        for sleutel, waarde in vervang.items():
            items = [i.replace(sleutel, waarde) for i in items]
        kopie_cfg, kopie_dir = wegwerpkopie(cfg)
        print(f"       (resolutieronde in de wegwerpkopie {kopie_dir.name}: eigen LocalData met de mmd-stores, ontkoppeling uit)")
        try:
            # De resolutieronde loopt alle items in een aanroep; GeoDmsRun lost ze eerst allemaal op.
            toets("3_boom", "resolutie_productie_items", items, cfg_override=kopie_cfg,
                  alleen_naamfouten=True, stop_bij_updating=True)
        finally:
            shutil.rmtree(kopie_dir, ignore_errors=True)
            shutil.rmtree(Path("C:/LocalData") / kopie_dir.name, ignore_errors=True)

    uit.mkdir(parents=True, exist_ok=True)
    with open(uit / "preflight.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["laag", "toets", "oordeel", "seconden", "melding"], delimiter=";")
        w.writeheader()
        w.writerows(regels)

    profiel_csv = next(uit.glob("profiel_*.csv"), None)
    if profiel_csv:
        fails = [r for r in profiel_csv.read_text(encoding="utf-8").splitlines()[1:] if r.endswith("FAIL")]
        if fails:
            print("\nAfwijkende parameters:")
            for r in fails:
                naam, verwacht, werkelijk, _ = next(csv.reader([r]))
                print(f"  {naam}: staat op {werkelijk}, profiel verwacht {verwacht}")

    mislukt = [r for r in regels if r["oordeel"] == "FAIL"]
    print(f"\n{len(regels) - len(mislukt)} van {len(regels)} toetsen geslaagd.")
    if mislukt:
        print("Deze run hoort niet te starten; zie " + str(uit / "preflight.csv"))
    return 1 if mislukt else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
