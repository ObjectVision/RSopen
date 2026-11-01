"""Vergelijkt twee uitvoermappen van RSopen en zegt wat er is veranderd.

Gebruik:
    python VergelijkUitvoer.py <map A> <map B> [opties]

Opties:
    --patroon <glob>   welke bestanden, relatief aan de mappen; default **/*.tif
    --tol <n>          relatieve tolerantie op de som; default 1e-9
    --max <n>          hoogstens zoveel bestanden vergelijken; default 0, dus alle
    --csv <pad>        schrijf de tabel ook als csv

Waarvoor: een versiewissel van GeoDMS of een wijziging in cfg mag de uitkomst niet stil veranderen. Dit
script legt twee runs naast elkaar en zegt per bestand of het gelijk is, en zo niet hoeveel het scheelt.
Bedoeld voor het commit-vergelijk-instrument uit model-RSopen#16 en voor de versiewissel uit #53.

Per bestand worden vier dingen vergeleken: de som, het aantal cellen met een waarde, het maximum en de
grootste absolute afwijking per cel. De som alleen is niet genoeg, want twee kaarten met dezelfde som
kunnen ruimtelijk verschillen; de grootste celafwijking vangt dat. Bestanden die maar in een van beide
mappen staan worden apart gemeld, want dat is meestal het echte nieuws.

Geheugen: de grids worden per paar ingelezen, twee tegelijk. Op het 25m-raster van Nederland is dat
ongeveer 1,2 GB per paar in float64; met --max is dat te beperken.
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import rasterio


def som_en_vorm(pad: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(pad) as s:
        a = s.read(1).astype(np.float64)
        if s.nodata is not None:
            a[a == s.nodata] = np.nan
    return a, {"cellen": int(np.count_nonzero(~np.isnan(a) & (a != 0))),
               "som": float(np.nansum(a)),
               "max": float(np.nanmax(a)) if np.any(~np.isnan(a)) else 0.0}


def vergelijk(a_pad: Path, b_pad: Path, tol: float) -> dict:
    a, ka = som_en_vorm(a_pad)
    b, kb = som_en_vorm(b_pad)
    if a.shape != b.shape:
        return {"oordeel": "VORM", "melding": f"{a.shape} tegenover {b.shape}", **ka}
    verschil = np.abs(np.nan_to_num(a) - np.nan_to_num(b))
    grootste = float(verschil.max()) if verschil.size else 0.0
    noemer = max(abs(ka["som"]), abs(kb["som"]), 1.0)
    relatief = abs(ka["som"] - kb["som"]) / noemer
    gelijk = grootste == 0.0
    return {"oordeel": "GELIJK" if gelijk else ("BINNEN_TOL" if relatief <= tol else "VERSCHIL"),
            "som_a": ka["som"], "som_b": kb["som"], "verschil_som": kb["som"] - ka["som"],
            "relatief": relatief, "grootste_cel": grootste,
            "cellen_a": ka["cellen"], "cellen_b": kb["cellen"]}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("map_a")
    ap.add_argument("map_b")
    ap.add_argument("--patroon", default="**/*.tif")
    ap.add_argument("--tol", type=float, default=1e-9)
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--csv")
    a = ap.parse_args(argv)

    A, B = Path(a.map_a), Path(a.map_b)
    in_a = {p.relative_to(A).as_posix(): p for p in A.glob(a.patroon)}
    in_b = {p.relative_to(B).as_posix(): p for p in B.glob(a.patroon)}
    alleen_a = sorted(set(in_a) - set(in_b))
    alleen_b = sorted(set(in_b) - set(in_a))
    beide = sorted(set(in_a) & set(in_b))
    if a.max:
        beide = beide[: a.max]

    print(f"A: {A}\nB: {B}\n{len(beide)} bestanden in beide, {len(alleen_a)} alleen in A, {len(alleen_b)} alleen in B\n")

    rijen = []
    for naam in beide:
        try:
            r = vergelijk(in_a[naam], in_b[naam], a.tol)
        except Exception as e:
            r = {"oordeel": "FOUT", "melding": str(e)[:120]}
        r["bestand"] = naam
        rijen.append(r)
        if r["oordeel"] != "GELIJK":
            extra = (f"som {r.get('som_a', 0):,.2f} -> {r.get('som_b', 0):,.2f} "
                     f"(verschil {r.get('verschil_som', 0):+,.2f}, relatief {r.get('relatief', 0):.2e}, "
                     f"grootste cel {r.get('grootste_cel', 0):g})") if "som_a" in r else r.get("melding", "")
            print(f"[{r['oordeel']:<10}] {naam}\n             {extra}")

    telling = {}
    for r in rijen:
        telling[r["oordeel"]] = telling.get(r["oordeel"], 0) + 1
    print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(telling.items())))
    for naam in alleen_a:
        print(f"[ALLEEN_A  ] {naam}")
    for naam in alleen_b:
        print(f"[ALLEEN_B  ] {naam}")

    if a.csv:
        velden = ["bestand", "oordeel", "som_a", "som_b", "verschil_som", "relatief", "grootste_cel", "cellen_a", "cellen_b", "melding"]
        with open(a.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=velden, delimiter=";", extrasaction="ignore")
            w.writeheader()
            w.writerows(rijen)
        print(f"\ntabel: {a.csv}")

    return 1 if (telling.get("VERSCHIL") or telling.get("VORM") or telling.get("FOUT") or alleen_a or alleen_b) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
