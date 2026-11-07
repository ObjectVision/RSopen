"""Hernoemt de ontkoppelde bestanden van een LocalData eenmalig naar hun naam met de hash van de fingerprint.

Gebruik:
    python OntkoppeldNaarHash.py <LocalData>               laat zien wat er zou gebeuren
    python OntkoppeldNaarHash.py <LocalData> --uitvoeren   hernoemt

Templates/DecoupledFile_T zet een hash over de fingerprint in de naam van een ontkoppeld bestand. Een bestand van
daarvoor heet nog zonder hash en wordt niet meer gelezen, dus zonder dit script maakt elke LocalData alles opnieuw,
terwijl de bestanden gewoon goed zijn. Het script leest per bestand het zijbestand en rekent daaruit de hash die de
configuratie zou rekenen. Klopt de fingerprint in dat zijbestand met de huidige invoer, dan vindt het model het
bestand op zijn nieuwe naam terug; klopt hij niet, dan is het bestand een oudere stand die niemand meer leest, wat het
ook al was. Er kan dus geen bestand onder een verkeerde fingerprint terechtkomen.

De basisjaarstand en de zonneladder zijn sets met een zijbestand naast een van de bestanden: de hele set krijgt de
hash van dat ene zijbestand. Het script schrijft niet buiten de opgegeven map en overschrijft niets.
"""

import argparse
import re
import sys
from pathlib import Path

# Gelijk aan Hash in cfg/main/Templates/DecoupledFile_T.dms.
ALFABET = ' !"#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~'
PRIEM = 2147483647
GRONDTAL = 16807
ZIJBESTAND = ".params.txt"
AL_GEHASHT = re.compile(r"_[0-9a-f]{8}$")
BIJBESTANDEN = (".tfw", ".xml")
SETMAPPEN = ("BaseData/StandBasisjaar", "BaseData/Grondgebruik/ZonneLadder")
MAPPEN = ("BaseData", "VariantData")


def fingerprint_hash(tekst: bytes) -> str:
    som = 0
    macht = 1
    for byte in tekst:
        teken = chr(byte)
        if teken in ALFABET:
            som += (ALFABET.index(teken) + 1) * macht
        macht = macht * GRONDTAL % PRIEM
    return f"{som % PRIEM:08x}"


def nieuwe_naam(pad: Path, hash_: str) -> Path:
    """<stam>.tif wordt <stam>_<hash>.tif, en <stam>.tif.params.txt wordt <stam>_<hash>.tif.params.txt."""
    stam, _, rest = pad.name.partition(".")
    return pad.with_name(f"{stam}_{hash_}.{rest}")


def bij_elkaar(bestand: Path) -> list[Path]:
    """Het bestand of de mmd-map, met wat GeoDMS ernaast schrijft."""
    stam = bestand.with_suffix("")
    paden = [bestand, Path(str(bestand) + ZIJBESTAND), Path(str(bestand) + ".params.xml")]
    paden += [Path(str(stam) + ext) for ext in BIJBESTANDEN]
    return [p for p in paden if p.exists()]


def plan(root: Path) -> list[tuple[Path, Path]]:
    zetten: list[tuple[Path, Path]] = []
    for map_ in MAPPEN:
        for zij in sorted((root / map_).rglob("*" + ZIJBESTAND)):
            bestand = Path(str(zij)[: -len(ZIJBESTAND)])
            if AL_GEHASHT.search(bestand.stem):
                continue
            hash_ = fingerprint_hash(zij.read_bytes())
            setmap = next((root / s for s in SETMAPPEN if (root / s) in zij.parents), None)
            if setmap is None:
                zetten += [(p, nieuwe_naam(p, hash_)) for p in bij_elkaar(bestand)]
            else:
                # De hele set: het zijbestand en elk bestand in de map dat nog geen hash draagt.
                for p in sorted(setmap.rglob("*")):
                    if p.is_file() and not AL_GEHASHT.search(p.name.partition(".")[0]):
                        zetten.append((p, nieuwe_naam(p, hash_)))
    return zetten


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("localdata", type=Path)
    ap.add_argument("--uitvoeren", action="store_true")
    a = ap.parse_args(argv)

    zetten = plan(a.localdata)
    bezet = [naar for _, naar in zetten if naar.exists()]
    if bezet:
        print(f"Gestopt: {len(bezet)} doelnamen bestaan al, bijvoorbeeld {bezet[0]}", file=sys.stderr)
        return 1
    for van, naar in zetten:
        print(f"{van.relative_to(a.localdata)} -> {naar.name}")
        if a.uitvoeren:
            van.rename(naar)
    print(f"{len(zetten)} namen {'gewijzigd' if a.uitvoeren else 'te wijzigen; geef --uitvoeren mee'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
