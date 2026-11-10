"""Zoekt de rode items in de hele boom: elk item buiten de templates waarvan de metainfo faalt.

Gebruik:
    python RodeItems.py <uitmap> [opties]

Opties:
    --cfg <pad>          de configuratie; default cfg/main.dms naast dit script
    --versie <naam>      de GeoDMS-map, bijvoorbeeld GeoDms20.28.0.m; default de versie uit batch/RunAll.cmd
    --wortel <pad>       begin bij dit item in plaats van bij de root; mag vaker
    --zonder <pad>       sla deze tak over; mag vaker
    --max-seconden <n>   stop na zoveel seconden; default 5400

De GUI kleurt een item rood wanneer UpdateMetaInfo faalt: een naam die niet oplost, een domein dat niet past, een
ontbrekend template-argument. Dit script doet hetzelfde met update_metainfo() uit de Python-binding van GeoDMS
(ObjectVision/GeoDMS#1279) en loopt daarna de sub-items af, zodat ook wat een meta-expressie of een for_each pas bij
het instantieren aanmaakt bezocht wordt. Modeldata wordt niet gerekend, maar een meta-expressie die data nodig heeft
voor haar keuze leest die wel.

Een meta-expressie kiest haar tak op de schakelaars van dit moment, dus de uitslag geldt voor de omgevingsvariabelen
van de aanroeper (StandAllocatieOntkoppeld, VariantDataOntkoppeld en de rest) en voor het productieprofiel van de
configuratie. Een lezer van een ontkoppeld bestand dat er niet is, is ook rood; draai daarom op een kopie met een eigen
mapnaam boven cfg, waarvan de LocalData de ontkoppelde bestanden van een recente run bevat. De boom van main telde op
10 november 2026 2,2 miljoen items, met een piek van 12,7 GB; een profiel met meer varianten deel je op met --wortel
en --zonder, een proces per variant.

Uitvoer in <uitmap>: rood.csv met pad en melding, plekken.txt met een telling per tak en de meest voorkomende
melding, en voortgang.txt. Zie pbl-nl/model-RSopen#53.
"""

import argparse
import csv
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


def projdir() -> Path:
    return Path(__file__).resolve().parent.parent


def versie_uit_runall() -> str:
    """De GeoDMS-versie die RunAll.cmd zet, zodat dit script niet op een andere versie toetst dan de runs."""
    tekst = (projdir() / "batch" / "RunAll.cmd").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^set geodmsversion=(\S+)", tekst, re.M)
    return m.group(1) if m else "GeoDms20.28.0.m"


def plek(pad: str) -> str:
    """De tak waarin een rood item zit, met zichtjaar, iteratie en sequentie weggelaten, voor de telling."""
    q = re.sub(r"/Y\d{4}\b", "/Yjjjj", pad)
    q = re.sub(r"/Iter_\d+", "/Iter_N", q)
    q = re.sub(r"/Seq_\d+", "/Seq_N", q)
    m = re.match(r"^/Allocatie/[^/]+/Zichtjaren/Yjjjj/Sequences/Seq_N/SectorAllocRegios/[^/]+_([A-Za-z]+)/(Iters_[A-Za-z]+)", q)
    if m:
        return f"/Allocatie/<casus>/.../SectorAllocRegios/<regio>_{m.group(1)}/{m.group(2)}"
    return "/".join(q.split("/")[:5])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("uit", type=Path)
    ap.add_argument("--cfg", default=str(projdir() / "cfg" / "main.dms"))
    ap.add_argument("--versie")
    ap.add_argument("--wortel", action="append", default=[])
    ap.add_argument("--zonder", action="append", default=[])
    ap.add_argument("--max-seconden", type=int, default=5400)
    a = ap.parse_args(argv)

    g = rf"C:\Program Files\ObjectVision\{a.versie or versie_uit_runall()}"
    if not Path(g).is_dir():
        print(f"GeoDMS niet gevonden: {g}", file=sys.stderr)
        return 2
    # Zonder de GeoDMS-map op PATH faalt het laden van de gdal-dll's bij elk item met een gdal-storage.
    os.environ["PATH"] = g + ";" + os.environ["PATH"]
    os.add_dll_directory(g)
    sys.path.insert(0, g)
    import geodms

    a.uit.mkdir(parents=True, exist_ok=True)
    start = time.time()
    # Engine en Config in een variabele houden: anders ruimt Python ze op en crasht de eerste aanroep.
    engine = geodms.Engine()
    config = engine.load_config(a.cfg)
    root = config.const_root()
    voortgang = open(a.uit / "voortgang.txt", "w", encoding="utf-8", buffering=1)
    voortgang.write(f"{geodms.version()}\n{a.cfg}\ngeladen in {time.time() - start:.1f} s\n")

    rood: dict[str, str] = {}
    bezocht = templates = 0
    stapel = [root.find(w) for w in a.wortel] if a.wortel else [root]
    zonder = tuple(z.rstrip("/") for z in a.zonder)
    afgebroken = ""
    while stapel:
        item = stapel.pop()
        if item.is_null():
            continue
        if item.in_template():
            templates += 1
            continue
        naam = item.full_name()
        if zonder and any(naam == z or naam.startswith(z + "/") for z in zonder):
            continue
        bezocht += 1
        try:
            if not item.update_metainfo():
                rood[naam] = " | ".join(item.fail_reason().splitlines())[:2000]
            stapel.extend(reversed(item.sub_items()))
        except Exception as e:  # noqa: BLE001, een item dat de binding niet aankan telt als rood
            rood[naam] = f"uitzondering: {e}"
        if bezocht % 10000 == 0:
            voortgang.write(f"{time.time() - start:7.0f} s  {bezocht} items  {len(rood)} rood  laatst {naam}\n")
        if time.time() - start > a.max_seconden:
            afgebroken = f"afgebroken na {a.max_seconden} s, "
            break

    with open(a.uit / "rood.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["pad", "melding"])
        w.writerows(sorted(rood.items()))
    per_plek: dict[str, list[str]] = defaultdict(list)
    for pad in rood:
        per_plek[plek(pad)].append(pad)
    with open(a.uit / "plekken.txt", "w", encoding="utf-8") as f:
        f.write(f"{len(rood)} rode items van {bezocht} bezochte, in {len(per_plek)} takken\n")
        for p, paden in sorted(per_plek.items(), key=lambda x: -len(x[1])):
            meld = Counter(re.sub(r"\[\[[^\]]*\]\]", "", rood[q]).split("|")[0].strip()[:120] for q in paden)
            f.write(f"{len(paden):8} {p}\n         {meld.most_common(1)[0][0]}\n         bv. {min(paden, key=len)}\n")
    voortgang.write(f"KLAAR {afgebroken}{time.time() - start:.0f} s  {bezocht} items  {len(rood)} rood  {templates} templates overgeslagen\n")
    print(f"{len(rood)} rode items van {bezocht} bezochte; zie {a.uit / 'plekken.txt'}")
    return 1 if rood else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
