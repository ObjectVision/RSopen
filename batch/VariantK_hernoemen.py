"""Hernoemt de rijen van VariantK volgens VariantK_namen.csv en haalt de rijen weg die niets doen (#638).

Gebruik, in de root van een werkkopie:
    python batch/VariantK_hernoemen.py               laat per bestand zien wat er zou veranderen
    python batch/VariantK_hernoemen.py --uitvoeren   past de bestanden aan

Op een projecttak: haal eerst main binnen tot de commit vlak voor de hernoeming, draai dan dit script met --uitvoeren en
commit dat apart, en haal daarna de rest van main binnen. Dan staan de nieuwe namen ook in de eigen kolommen van de
projecttak, en botst alleen wat de tak zelf anders heeft naast een hernoemde regel: altijd VariantK.dms, soms een
bestand met een eigen instelling. Kies in die conflicten de kant van de projecttak, want daar heeft het script de namen
al aangepast. Draai het script daarna nog eens zonder --uitvoeren: het verandert dan niets, en wijst een lezer naar een
rij die niet in VariantK staat, dan heeft main die rij gekregen en hoort hij er met de hand bij, in de kolommen van de
eigen varianten. Blijft er na afloop een oude naam staan, dan schrijft het script niets.

In VariantK.dms en ExportSettings.dms vervangt het script elke oude naam als heel woord, ongeacht hoofdletters (GeoDMS
ook), zodat de rij en de kolom van de parameterexport dezelfde nieuwe naam krijgen. In de andere dms-bestanden en de
scripts onder batch vervangt het alleen verwijzingen die met VariantK/ beginnen; een lokale alias met de oude naam blijft
staan, want een alias met de nieuwe naam kan in zijn sjabloon een ander item met die naam afschermen. In een Descr of
commentaarregel van die bestanden telt alleen de schrijfwijze van de rij zelf, zodat een gewoon woord blijft. Volgt er een
uitlijning met spaties, dan blijft de volgende kolom op zijn plaats. Een lezer die de naam zelf samenstelt
('RestrictiesVariant_' + sector) heeft een vaste vervanging in SAMENGESTELD. De rijen zonder nieuwe naam gaan weg uit
VariantK.dms en ExportSettings.dms. Vooraf toetst het dat geen nieuwe naam al een rij of exportkolom is, en achteraf dat
geen verwijzing via VariantK/ en geen samengestelde vorm met een oude naam is blijven staan; andere plekken waar een oude
naam nog als woord staat, zoals een alias of een Descr, meldt het ter controle. Het schrijft in bytes, dus regeleindes en
de afwezigheid van een BOM blijven zoals ze waren.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
ROOT = HIER.parent
AFBEELDING = HIER / "VariantK_namen.csv"
VARIANTK = Path("cfg/main/VariantParameters/VariantK.dms")
EXPORT = Path("cfg/main/ExportSettings.dms")

# Lezers die de naam uit een voorvoegsel en een sector, klasse of zone samenstellen. Per regel: bestand, oude tekst,
# nieuwe tekst. Een regel die niet past wordt gemeld; op een projecttak komt de lezer dan met main mee.
SAMENGESTELD = [
    ("cfg/main/Templates/VariantData/MaakRestrictieCombinaties_T.dms",
     "VariantK/RestrictiesVariant_'+Sector", "VariantK/Restricties_'+Sector"),
    ("cfg/main/Templates/VariantData/MaakRestrictieCombinaties_T.dms",
     "RestrictiesVariant_<sector>", "Restricties_<sector>"),
    ("cfg/main/Templates/VariantData/MaakStimuliCombinaties_T.dms",
     "VariantK/StimuliVariant_'+Sector", "VariantK/Stimuli_'+Sector"),
    ("cfg/main/VariantParameters/Tredes.dms",
     "VariantK/StimuliVariant_<sector>", "VariantK/Stimuli_<sector>"),
    ("cfg/main/Templates/Allocatie/Zichtjaar_T.dms",
     "VariantK/Groeifactor_'+", "VariantK/GroeiFootprintPerBaan_'+"),
    ("cfg/main/Templates/Densities/DichtheidZichtjaar_T.dms",
     "VariantK/Groeifactor_'+", "VariantK/GroeiFootprintPerBaan_'+"),
    ("cfg/main/Templates/Landbouw/Akkerbouw_T.dms",
     "VariantK/PriceMult_'+", "VariantK/Prijsfactor_'+"),
    ("cfg/main/Templates/Beschikbaarheden/Zeef_Basisjaar_T.dms",
     "'VariantK/NietBouwenInZeerMooiLandschap'+Sector_name", "'VariantK/NietBouwenInZeerMooiLandschap_'+Sector_name"),
    ("cfg/main/Templates/Beschikbaarheden/Zeef_T.dms",
     "parameter<Float32> MinimumDichtheidToenameSector        := ='VariantK/MinimumDichtheidToename'+Sector_name+'[Variant_rel]';",
     "parameter<Float32> MinimumDichtheidToenameSector        := =Sector_name == 'werken' ? 'VariantK/MinimumDichtheidToename_Werken[Variant_rel]' : '0f'"
     ", Descr = \"De minimale toename van de werkgelegenheid in een cel waaronder de zeef hem afwijst; alleen werken kent die toets, wonen heeft de zijne in Zeef_Wonen_perOP_T.\";"),
    ("cfg/main/Templates/VariantData_T.dms",
     "AsItemList('VariantParameters/VariantK/GevaarRegimeZone'+string(id(Classifications/Overstromingsgevaarzonering/zoneringK))+'[VariantParameters/VariantK/V/'+Variant_name+']')",
     "AsItemList('VariantParameters/VariantK/BouwregimeOverstroming_'+Classifications/Overstromingsgevaarzonering/zoneringK/name+'[VariantParameters/VariantK/V/'+Variant_name+']')"),
    ("cfg/main/Templates/VariantData_T.dms",
     "uit de zes VariantK-parameters GevaarRegimeZone0 tot en met 5. Die worden op volgnummer aan de zones gekoppeld, dus een zone erbij of eraf verschuift ze stil; daarom staat er bij GevaarRegimeZone0 een IntegrityCheck op het aantal zones.",
     "uit de VariantK-parameters BouwregimeOverstroming_<zone>, opgezocht op de naam van de zone, zodat een zone erbij of eraf geen rij stil verschuift; een zone zonder rij geeft een fout. Bij BouwregimeOverstroming_Nihil staat daarnaast een IntegrityCheck op het aantal zones."),
    ("cfg/main/Templates/VariantData_T.dms",
     "VariantParameters/VariantK/GevaarRegimeZone0 tot en met 5", "VariantParameters/VariantK/BouwregimeOverstroming_<zone>"),
    ("cfg/main/Templates/VariantData_T.dms",
     "VariantParameters/VariantK/GevaarRegimeZone'+string(id(/Classifications/Overstromingsgevaarzonering/zoneringK))+'",
     "VariantParameters/VariantK/BouwregimeOverstroming_'+/Classifications/Overstromingsgevaarzonering/zoneringK/name+'"),
    ("cfg/main/Templates/VariantData_T.dms",
     "GevaarRegimeZone0 en 1 staan overal op Bouwen en 2 tot en met 5 op",
     "de zones Nihil en Gering_20 staan overal op Bouwen en de zones Gering_200 tot en met Zeer_gevaarlijk op"),
    ("cfg/main/ModelParameters.dms",
     "VariantK/StimuliVariant_<sector>", "VariantK/Stimuli_<sector>"),
    ("cfg/main/Templates/Suitabilities/Suitability_Zichtjaar_T.dms",
     "VariantK/Weight_*_Waterberging", "VariantK/Gewicht_*_Waterberging"),
]

# Rijen die een lezer per sector, klasse of zone samenstelt. Een projecttak kan zo'n rij hebben voor een eigen sector die
# niet in VariantK_namen.csv staat; die krijgt dan de nieuwe vorm volgens dit patroon. Een lege vervanging betekent weg:
# de minimale dichtheidstoename leest de zeef alleen voor werken, en wonen heeft de zijne in Zeef_Wonen_perOP_T.
PATRONEN = [
    (r"RestrictiesVariant_(\w+)", r"Restricties_\1"),
    (r"StimuliVariant_(\w+)", r"Stimuli_\1"),
    (r"MinimumDichtheidToename(Wonen|Werken)", r"MinimumDichtheidToename_\1"),
    (r"MinimumDichtheidToename(?!_)(\w+)", ""),
    (r"NietBouwenInZeerMooiLandschap(?!_)(\w+)", r"NietBouwenInZeerMooiLandschap_\1"),
    (r"Groeifactor_(\w+)", r"GroeiFootprintPerBaan_\1"),
    (r"PriceMult_(\w+)", r"Prijsfactor_\1"),
]

# Wat na afloop nergens meer mag staan: de samengestelde vormen van de oude namen.
VERBODEN_VORMEN = ["RestrictiesVariant_'", "StimuliVariant_'", "VariantK/Groeifactor_'", "VariantK/PriceMult_'",
                   "VariantK/GevaarRegimeZone'", "VariantK/MinimumDichtheidToename'", "NietBouwenInZeerMooiLandschap'+"]


def lees_afbeelding() -> tuple[dict[str, str], list[str]]:
    hernoem: dict[str, str] = {}
    weg: list[str] = []
    with open(AFBEELDING, encoding="utf-8", newline="") as f:
        for rij in csv.DictReader(f, delimiter=";"):
            if rij["nieuw"]:
                hernoem[rij["oud"]] = rij["nieuw"]
            else:
                weg.append(rij["oud"])
    return hernoem, weg


def volgens_patroon(variantk: bytes, hernoem: dict[str, str], weg: list[str]) -> list[str]:
    """Vult de afbeelding aan met de rijen in VariantK.dms die een patroon volgen maar niet in de lijst staan."""
    bekend = {n.lower() for n in list(hernoem) + list(hernoem.values()) + weg}
    erbij = []
    for m in re.finditer(rb"^\s*(?:attribute|parameter)<[^>]+>\s*([A-Za-z_][A-Za-z0-9_]*)", variantk, re.MULTILINE):
        naam = m.group(1).decode()
        if naam.lower() in bekend:
            continue
        for patroon, vervanging in PATRONEN:
            if re.fullmatch(patroon, naam):
                if vervanging:
                    hernoem[naam] = re.sub(patroon, vervanging, naam)
                    erbij.append(f"{naam} -> {hernoem[naam]}")
                else:
                    weg.append(naam)
                    erbij.append(f"{naam} weg")
                bekend.add(naam.lower())
                break
    return erbij


def bestanden(root: Path) -> list[Path]:
    lijst = sorted((root / "cfg").rglob("*.dms"))
    lijst += [p for p in sorted((root / "batch").glob("*")) if p.suffix in (".ps1", ".py", ".cmd") and p.name != Path(__file__).name]
    return lijst


def woord(naam: str, voor: bytes = b"") -> re.Pattern:
    """De naam als heel woord, ongeacht hoofdletters, eventueel na het voorvoegsel voor, met de spaties erachter (voor de uitlijning)."""
    return re.compile(rb"(?<![A-Za-z0-9_])" + re.escape(voor) + re.escape(naam.encode()) + rb"(?![A-Za-z0-9_])( {2,})?", re.IGNORECASE)


def vervang(tekst: bytes, oud: str, nieuw: str, voor: bytes = b"") -> tuple[bytes, int]:
    def zet(m: re.Match) -> bytes:
        spaties = m.group(1)
        if spaties is None:
            return voor + nieuw.encode()
        breedte = len(oud) + len(spaties)
        return voor + nieuw.encode() + b" " * max(breedte - len(nieuw), 1)
    return woord(oud, voor).subn(zet, tekst)


TEKST = re.compile(rb'Descr\s*=\s*"[^"]*"|//[^\n]*', re.IGNORECASE)


def in_tekst(tekst: bytes, oud: str, nieuw: str) -> tuple[bytes, int]:
    """Vervangt de oude naam in een Descr of een commentaarregel, waar hij de rij van VariantK noemt en geen alias is.
    In tekst telt alleen de schrijfwijze van de rij zelf, anders wordt een gewoon woord als 'turbinetype' mee hernoemd."""
    teller = 0
    patroon = re.compile(woord(oud).pattern)
    def zet(m: re.Match) -> bytes:
        nonlocal teller
        stuk, n = patroon.subn(lambda w: nieuw.encode() + (w.group(1) or b""), m.group(0))
        teller += n
        return stuk
    return TEKST.sub(zet, tekst), teller


def haal_rijen_weg(tekst: bytes, namen: list[str], pad: Path) -> tuple[bytes, list[str]]:
    """Haalt de declaratie van elke naam weg, ook als die over meer regels loopt (tot de puntkomma aan het eind)."""
    if not namen:
        return tekst, []
    regels = tekst.split(b"\n")
    uit: list[bytes] = []
    weg: list[str] = []
    i = 0
    kop = re.compile(rb"^\s*(attribute|parameter)<[^>]+>\s+(" + b"|".join(re.escape(n.encode()) for n in namen) + rb")(?![A-Za-z0-9_])", re.IGNORECASE)
    while i < len(regels):
        m = kop.match(regels[i])
        if not m:
            uit.append(regels[i]); i += 1; continue
        weg.append(m.group(2).decode())
        while not re.search(rb';\s*(//[^"]*)?\r?$', regels[i]):
            i += 1
        i += 1
    return b"\n".join(uit), weg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uitvoeren", action="store_true", help="pas de bestanden aan; zonder deze vlag alleen een overzicht")
    ap.add_argument("--root", type=Path, default=ROOT, help="de werkkopie, standaard die van dit script")
    a = ap.parse_args()
    root = a.root.resolve()
    hernoem, weg = lees_afbeelding()
    paden = bestanden(root)
    inhoud = {p: p.read_bytes() for p in paden}
    if root / VARIANTK in inhoud:
        erbij = volgens_patroon(inhoud[root / VARIANTK], hernoem, weg)
        if erbij:
            print("Niet in de lijst, wel volgens een patroon:\n    " + "\n    ".join(erbij))

    eigen = {root / VARIANTK, root / EXPORT}
    verwijzing = b"VariantK/"

    # Een paar waarvan de oude naam nergens meer staat, is al hernoemd; zo kan het script ook een tweede keer draaien.
    def staat_er(oud: str) -> bool:
        return any(woord(oud).search(t) if p in eigen else woord(oud, verwijzing).search(t) for p, t in inhoud.items())
    hernoem = {o: n for o, n in hernoem.items() if staat_er(o)}
    weg = [o for o in weg if staat_er(o)]

    # Een nieuwe naam die al een rij of exportkolom is, zou na het hernoemen met die rij samenvallen.
    botsing = []
    for oud, nieuw in hernoem.items():
        if oud.lower() == nieuw.lower():
            continue
        rij = re.compile(rb"(attribute|parameter)<[^>]*>\s+" + re.escape(nieuw.encode()) + rb"(?![A-Za-z0-9_])", re.IGNORECASE)
        for p in eigen:
            if p in inhoud and rij.search(inhoud[p]):
                botsing.append(f"{nieuw} (voor {oud}) staat al in {p.relative_to(root)}")
        for p, t in inhoud.items():
            if woord(nieuw, verwijzing).search(t):
                botsing.append(f"VariantK/{nieuw} (voor {oud}) staat al in {p.relative_to(root)}")
    if botsing:
        print("Gestopt: deze nieuwe namen bestaan al.\n  " + "\n  ".join(botsing))
        return 1

    nieuw_inhoud = dict(inhoud)
    per_bestand: dict[Path, list[str]] = {}
    for bestand, oud_tekst, nieuw_tekst in SAMENGESTELD:
        p = root / bestand
        # De uitlijning verschilt per tak, dus elke reeks spaties of tabs in de oude tekst mag een andere lengte hebben.
        oud_re = re.compile(rb"[ \t]+".join(re.escape(stuk.encode()) for stuk in oud_tekst.split()))
        if p not in nieuw_inhoud or not oud_re.search(nieuw_inhoud[p]):
            if p in nieuw_inhoud and nieuw_tekst.encode() not in nieuw_inhoud[p]:
                print(f"Let op: de samengestelde lezer past niet in {bestand}: {oud_tekst[:70]}")
            continue
        nieuw_inhoud[p], n = oud_re.subn(lambda m: nieuw_tekst.encode(), nieuw_inhoud[p])
        per_bestand.setdefault(p, []).append(f"samengesteld {oud_tekst[:50]} ({n})")

    for p in (root / VARIANTK, root / EXPORT):
        if p in nieuw_inhoud:
            nieuw_inhoud[p], weg_hier = haal_rijen_weg(nieuw_inhoud[p], weg, p)
            if weg_hier:
                per_bestand.setdefault(p, []).append("weg: " + ", ".join(weg_hier))

    for p in nieuw_inhoud:
        for oud, nieuw in hernoem.items():
            nieuw_inhoud[p], n = vervang(nieuw_inhoud[p], oud, nieuw, b"" if p in eigen else verwijzing)
            if p.suffix in (".ps1", ".py", ".cmd"):
                for q in (b"'", b'"'):
                    nieuw_inhoud[p], m = vervang(nieuw_inhoud[p], oud, nieuw, q)
                    n += m
            nieuw_inhoud[p], m = in_tekst(nieuw_inhoud[p], oud, nieuw)
            n += m
            if n:
                per_bestand.setdefault(p, []).append(f"{oud} -> {nieuw} ({n})")

    # De ja/nee-rij ExogeenOpleggen staat als tekst; als ja/nee is hij gelijk en leesbaarder.
    p = root / VARIANTK
    nieuw_inhoud[p] = re.sub(rb"(attribute<Bool>\s+ExogeenOpleggen\s*:\s*\[)([^\]]*)(\])",
                             lambda m: m.group(1) + m.group(2).replace(b"'", b"") + m.group(3), nieuw_inhoud[p])

    over = []
    controle = []
    for p, t in nieuw_inhoud.items():
        for oud, nieuw in hernoem.items():
            if oud.lower() == nieuw.lower():
                continue
            if woord(oud, verwijzing).search(t) or (p in eigen and woord(oud).search(t)):
                over.append(f"{oud} in {p.relative_to(root)}")
            elif woord(oud).search(t):
                regels = [i + 1 for i, r in enumerate(t.split(b"\n")) if woord(oud).search(r)]
                controle.append(f"{oud} in {p.relative_to(root)}, regel {', '.join(map(str, regels))}")
        for naam in weg:
            if woord(naam).search(t):
                over.append(f"{naam} (weg) in {p.relative_to(root)}")
        for vorm in VERBODEN_VORMEN:
            if vorm.lower().encode() in t.lower():
                over.append(f"samengesteld {vorm} in {p.relative_to(root)}")

    # Na een merge van main kan een lezer naar een rij wijzen die alleen main heeft; die rij hoort er dan met de hand bij,
    # in de kolommen van de eigen varianten. Een samengestelde naam (gevolgd door ' of @, of eindigend op _) telt niet mee.
    rijen = {m.group(1).decode().lower() for m in re.finditer(rb"^\s*(?:attribute|parameter|container|unit)\s*(?:<[^>]*>)?\s*([A-Za-z_]\w*)",
                                                     nieuw_inhoud.get(root / VARIANTK, b""), re.MULTILINE)}
    ontbreekt: dict[str, set[str]] = {}
    for p, t in nieuw_inhoud.items():
        for regel in t.split(b"\n"):
            code = regel.split(b"//", 1)[0]
            for m in re.finditer(rb"VariantK/([A-Za-z_]\w*)(?!['@\w])", code):
                naam = m.group(1).decode()
                if not naam.endswith("_") and naam.lower() not in rijen:
                    ontbreekt.setdefault(naam, set()).add(str(p.relative_to(root)))

    for p, wat in per_bestand.items():
        print(f"{p.relative_to(root)}:")
        for w in wat:
            print(f"    {w}")
    gewijzigd = [p for p in nieuw_inhoud if nieuw_inhoud[p] != inhoud[p]]
    print(f"{len(gewijzigd)} bestanden veranderen.")
    if controle:
        print("Nog als woord aanwezig, ter controle (alias of tekst):\n  " + "\n  ".join(controle))
    if ontbreekt:
        print("Let op: deze lezers wijzen naar een rij die niet in VariantK staat:\n  "
              + "\n  ".join(f"{n} in {', '.join(sorted(ps))}" for n, ps in sorted(ontbreekt.items())))
    if over:
        print("Blijft staan:\n  " + "\n  ".join(over))
        if a.uitvoeren:
            print("Niet uitgevoerd: een half hernoemde tak laadt niet meer. Los eerst op wat blijft staan.")
        return 1
    if a.uitvoeren:
        for p in gewijzigd:
            p.write_bytes(nieuw_inhoud[p])
        print("Uitgevoerd.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
