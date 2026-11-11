"""Toont per ontkoppeld bestand de oudere standen met hun omvang, en verwijdert ze pas na akkoord.

Gebruik:
    python OntkoppeldOpruimen.py <LocalData>                          toont de oudere standen en schrijft ze in een lijst
    python OntkoppeldOpruimen.py <LocalData> --in-gebruik <bestand>   idem, en bewaart ook wat in dat bestand genoemd wordt
    python OntkoppeldOpruimen.py <LocalData> --verwijderen <lijst>    verwijdert precies wat in die lijst staat

Templates/DecoupledFile_T zet een hash van de fingerprint in de naam van een ontkoppeld bestand, dus elke stand van de
invoer krijgt een eigen bestand en een wissel van variant of instelling gooit niets weg (#878). De keerzijde is dat
oudere standen blijven staan; een extra volledige stand voor Nederland kost ongeveer 5 GB. Dit script zet per naam,
het pad zonder hash, de standen onder elkaar: de hash, de datum, de omvang met de bijbestanden, en welke sleutels van
de fingerprint verschillen van die van de nieuwste stand. Aan dat verschil zie je of een oudere stand nog terug kan
komen (een andere variant of instelling) of door de code is ingehaald (een hogere rule, een nieuwe levering).

De nieuwste stand per naam blijft altijd staan. Met --in-gebruik blijft ook elke stand staan die in dat bestand
genoemd wordt; geef daar de lijst van .claude/skills/rs-draaien/scripts/naamcontrole.ps1 -Bestanden, eventueel een
per variant, dan blijft staan wat de configuratie op dit moment leest of schrijft. De rest komt in een lijst in
<LocalData>/logs. Verwijderen gaat in een tweede aanroep met precies die lijst: het script toetst eerst of elk pad
nog dezelfde omvang en datum heeft als in de lijst, en of er geen GeoDMS-proces op deze LocalData draait, en
verwijdert anders niets. Zo is wat verwijderd wordt gelijk aan wat er getoond en goedgekeurd is.

Een bestand telt alleen als stand wanneer de hash in zijn naam gelijk is aan de hash over de inhoud van een zijbestand
met dezelfde hash. Een datum van acht cijfers aan het eind van een naam, zoals bij een levering, valt daardoor
buiten de telling. Een stand zonder zijbestand, achtergelaten door een afgebroken run, telt mee als er onder dezelfde
naam ook een stand met zijbestand staat. Het script kijkt in BaseData en VariantData; de standen van de allocatie en
de indicatoren hebben geen fingerprint en geen hash en vallen erbuiten.
"""

import argparse
import csv
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Gelijk aan Hash in cfg/main/Templates/DecoupledFile_T.dms en aan batch/OntkoppeldNaarHash.py.
ALFABET = ' !"#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~'
PRIEM = 2147483647
GRONDTAL = 16807
ZIJBESTAND = ".params.txt"
HASH = re.compile(r"^(?P<basis>.*)_(?P<hash>[0-9a-f]{8})$")
MAPPEN = ("BaseData", "VariantData")
VELDEN = ["pad", "bytes", "mtime"]


def fingerprint_hash(tekst: bytes) -> str:
    som = 0
    macht = 1
    for byte in tekst:
        teken = chr(byte)
        if teken in ALFABET:
            som += (ALFABET.index(teken) + 1) * macht
        macht = macht * GRONDTAL % PRIEM
    return f"{som % PRIEM:08x}"


def omvang(pad: Path) -> int:
    if pad.is_dir():
        return sum(p.stat().st_size for p in pad.rglob("*") if p.is_file())
    return pad.stat().st_size


def mtime(pad: Path) -> float:
    if pad.is_dir():
        return max([pad.stat().st_mtime] + [p.stat().st_mtime for p in pad.rglob("*") if p.is_file()])
    return pad.stat().st_mtime


def sleutels(fingerprint: str) -> dict[str, str]:
    """sleutel=waarde gescheiden door puntkomma's. Een deel zonder = hoort bij de waarde ervoor, want een geneste
    fingerprint of een lijst kan zelf een puntkomma bevatten."""
    uit: dict[str, str] = {}
    vorige = None
    for deel in fingerprint.split(";"):
        sleutel, is_, waarde = deel.partition("=")
        if is_ and re.fullmatch(r"[A-Za-z0-9_]+", sleutel):
            uit[sleutel] = waarde
            vorige = sleutel
        elif vorige is not None:
            uit[vorige] += ";" + deel
    return uit


def verschil(oud: str | None, nieuw: str | None, breedte: int = 40) -> str:
    if oud is None or nieuw is None:
        return "geen zijbestand"
    a, b = sleutels(oud), sleutels(nieuw)

    def kap(s: str) -> str:
        return s if len(s) <= breedte else s[: breedte - 3] + "..."

    delen = []
    for k in list(b) + [k for k in a if k not in b]:
        if a.get(k) != b.get(k):
            delen.append(f"{k} {kap(a.get(k, '(geen)'))} -> {kap(b.get(k, '(geen)'))}")
    return "; ".join(delen) if delen else "zelfde fingerprint"


def standen(root: Path) -> dict[Path, dict[str, list[Path]]]:
    """Per naam zonder hash: per hash de paden die bij die stand horen (het bestand of de mmd-map plus wat GeoDMS
    ernaast schrijft)."""
    geldig: set[str] = set()
    kandidaten: list[tuple[Path, str, str]] = []
    for map_ in MAPPEN:
        if not (root / map_).exists():
            continue
        for pad in (root / map_).rglob("*"):
            if any(p.suffix == ".mmd" and p.is_dir() for p in pad.parents if root in p.parents):
                continue  # de inhoud van een mmd-map hoort bij die map
            stam, punt, rest = pad.name.partition(".")
            m = HASH.match(stam)
            if not m:
                continue
            kandidaten.append((pad, m["basis"] + punt + rest, m["hash"]))
            if pad.name.endswith(ZIJBESTAND) and pad.is_file() and fingerprint_hash(pad.read_bytes()) == m["hash"]:
                geldig.add(m["hash"])

    groepen: dict[Path, dict[str, list[Path]]] = {}
    for pad, naam_zonder_hash, hash_ in kandidaten:
        # De naam van een stand is die van het hoofdbestand: zonder .params.txt, .params.xml, .tfw of .xml erachter.
        naam = re.sub(r"(\.params\.txt|\.params\.xml)$", "", naam_zonder_hash)
        groepen.setdefault(pad.parent / naam, {}).setdefault(hash_, []).append(pad)

    # Bijbestanden als .tfw en .xml dragen een andere extensie dan het hoofdbestand; hang ze aan het hoofdbestand
    # met dezelfde stam en hash.
    for sleutel in list(groepen):
        if sleutel.suffix.lower() in (".tfw", ".xml"):
            for hoofd in groepen:
                if hoofd != sleutel and hoofd.parent == sleutel.parent and hoofd.name.partition(".")[0] == sleutel.name.partition(".")[0] \
                        and hoofd.suffix.lower() not in (".tfw", ".xml"):
                    for h, paden in groepen.pop(sleutel).items():
                        groepen[hoofd].setdefault(h, []).extend(paden)
                    break

    # Alleen namen met minstens een stand waarvan de hash klopt met een zijbestand.
    return {k: v for k, v in groepen.items() if any(h in geldig for h in v)}


def datum_van(paden: list[Path]) -> float:
    """Het moment waarop de stand af was: het zijbestand, want dat schrijft GeoDMS als laatste. Zonder zijbestand de
    jongste datum van de paden."""
    zij = [p for p in paden if p.name.endswith(ZIJBESTAND)]
    return mtime(zij[0]) if zij else max(mtime(p) for p in paden)


def fingerprint_van(paden: list[Path], per_hash: dict[str, str], hash_: str) -> str | None:
    zij = [p for p in paden if p.name.endswith(ZIJBESTAND)]
    if zij:
        return zij[0].read_text(encoding="utf-8", errors="replace")
    return per_hash.get(hash_)  # een lid van een set draagt de fingerprint van het zijbestand van de set


def lees_in_gebruik(bestanden: list[Path]) -> set[str]:
    uit: set[str] = set()
    for b in bestanden:
        for regel in b.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            regel = regel.strip()
            if regel and not regel.startswith("#"):
                uit.add(regel.replace("\\", "/").lower())
    return uit


def geodms_op(root: Path) -> list[str]:
    """GeoDMS-processen op deze LocalData. GeoDMS leidt de LocalData af uit C:/LocalData plus de naam van de map boven
    cfg; een proces waarvan die naam gelijk is aan die van root, of een GUI zonder configuratie op de commandoregel,
    houdt het verwijderen tegen."""
    cmd = ("Get-CimInstance Win32_Process -Filter \"Name='GeoDmsRun.exe' or Name='GeoDmsGuiQt.exe'\" | "
           "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    bezet = []
    for regel in r.stdout.splitlines():
        if not regel.strip():
            continue
        m = re.search(r"([^\\/\"]+)[\\/]cfg[\\/][^\\/\"]+\.dms", regel, re.I)
        if m is None or m.group(1).lower() == root.name.lower():
            bezet.append(regel.strip()[:200])
    return bezet


def toon(root: Path, in_gebruik: set[str], lijst: Path) -> int:
    groepen = standen(root)
    per_hash: dict[str, str] = {}
    for per in groepen.values():
        for h, paden in per.items():
            for p in paden:
                if p.name.endswith(ZIJBESTAND):
                    per_hash[h] = p.read_text(encoding="utf-8", errors="replace")

    weg: list[dict[str, str]] = []
    totaal = 0
    for naam in sorted(groepen, key=lambda p: str(p).lower()):
        per = groepen[naam]
        if len(per) < 2:
            continue
        rijen = sorted(((datum_van(paden), h, paden) for h, paden in per.items()), reverse=True)
        nieuwste_fp = fingerprint_van(rijen[0][2], per_hash, rijen[0][1])
        print(naam.relative_to(root))
        for i, (t, h, paden) in enumerate(rijen):
            bytes_ = sum(omvang(p) for p in paden)
            datum = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")
            gebruikt = any(str(p).replace("\\", "/").lower() in in_gebruik for p in paden)
            if i == 0:
                oordeel = "bewaren, nieuwste"
            elif gebruikt:
                oordeel = "bewaren, in gebruik"
            else:
                oordeel = "oud: " + verschil(fingerprint_van(paden, per_hash, h), nieuwste_fp)
                totaal += bytes_
                for p in paden:
                    weg.append({"pad": str(p), "bytes": str(omvang(p)), "mtime": f"{mtime(p):.0f}"})
            print(f"  {h}  {datum}  {bytes_ / 1e6:10.1f} MB  {oordeel}")
        print()

    namen = sum(1 for v in groepen.values() if len(v) > 1)
    print(f"{len(groepen)} namen met een hash, waarvan {namen} met meer dan een stand.")
    if not weg:
        print("Geen oudere standen om op te ruimen.")
        return 0
    lijst.parent.mkdir(parents=True, exist_ok=True)
    with open(lijst, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=VELDEN, delimiter=";")
        w.writeheader()
        w.writerows(weg)
    print(f"Oudere standen: {len(weg)} paden, samen {totaal / 1e9:.2f} GB, in {lijst}")
    print(f"Verwijderen, na akkoord: python {Path(__file__).name} {root} --verwijderen {lijst}")
    return 0


def verwijder(root: Path, lijst: Path) -> int:
    with open(lijst, encoding="utf-8", newline="") as f:
        rijen = list(csv.DictReader(f, delimiter=";"))
    fout = []
    for r in rijen:
        p = Path(r["pad"])
        if root.resolve() not in p.resolve().parents:
            fout.append(f"buiten {root}: {p}")
        elif not p.exists():
            fout.append(f"bestaat niet meer: {p}")
        elif str(omvang(p)) != r["bytes"] or f"{mtime(p):.0f}" != r["mtime"]:
            fout.append(f"veranderd sinds de lijst: {p}")
    bezet = geodms_op(root)
    if bezet:
        fout.append("er draait GeoDMS op deze LocalData, of een GUI waarvan dat niet te zien is:\n    " + "\n    ".join(bezet))
    if fout:
        print("Niets verwijderd:", file=sys.stderr)
        for regel in fout[:20]:
            print(f"  {regel}", file=sys.stderr)
        if len(fout) > 20:
            print(f"  ... en nog {len(fout) - 20}", file=sys.stderr)
        return 1
    totaal = 0
    for r in rijen:
        p = Path(r["pad"])
        totaal += int(r["bytes"])
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        print(f"verwijderd: {p.relative_to(root)}")
    print(f"{len(rijen)} paden verwijderd, samen {totaal / 1e9:.2f} GB.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("localdata", type=Path)
    ap.add_argument("--in-gebruik", type=Path, action="append", default=[])
    ap.add_argument("--lijst", type=Path)
    ap.add_argument("--verwijderen", type=Path)
    a = ap.parse_args(argv)

    if not a.localdata.is_dir():
        print(f"Geen map: {a.localdata}", file=sys.stderr)
        return 2
    if a.verwijderen:
        return verwijder(a.localdata, a.verwijderen)
    lijst = a.lijst or a.localdata / "logs" / f"oude_standen_{datetime.now():%Y%m%d_%H%M}.csv"
    return toon(a.localdata, lees_in_gebruik(a.in_gebruik), lijst)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
