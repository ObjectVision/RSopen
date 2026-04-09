#!/usr/bin/env python3
"""Update RSOpen file headers: contact info en beschrijvingen.

- Bestaande headers: alleen contact info bijwerken (beschrijving blijft intact)
- Bestanden zonder header: volledige header toevoegen met beschrijving o.b.v. bestandsinhoud
- Encoding: detecteert UTF-8 of cp1252, schrijft altijd UTF-8
- Lange beschrijvingsregels worden afgebroken op ~110 tekens met // vervolg
"""

import os
import re
import textwrap
from pathlib import Path

ROOT = Path(r"C:\ProjDir\RSopen\.claude\worktrees\exciting-mcnulty")

DMS_DIVIDER = "/" * 296
WRAP_WIDTH = 110  # max tekens per beschrijvingsregel (na "// ")

NEW_CONTACT_LINES = (
    "// Opdrachtgever/ontwikkelaar PBL: Bas van Bemmel (Bas.vanBemmel@pbl.nl)\n"
    "// Contactpersoon/ontwikkelaar Object Vision: Jip Claassens (jclaassens@objectvision.nl)\n"
    "// Contactpersoon/ontwikkelaar Deltares: Bart Rijken (bart.rijken@deltares.nl)\n"
)

KNOWN_DESCRIPTIONS = {
    "RunAll.cmd": (
        "Start een volledige RSopen modelrun: stelt paden en GeoDMS-versie in, vraagt of basedata "
        "hergebruikt kan worden en of alleen het eindjaar berekend moet worden, en roept daarna de "
        "deelscripts (PrepareBasedata, RunScenarios, RunVariantData) aan."
    ),
    "RunImpl.cmd": (
        "Generieke wrapper voor het aanroepen van GeoDmsRun.exe met een opgegeven DMS-container. "
        "Legt de starttijd vast, voert de berekening uit en schrijft het resultaat naar het logbestand."
    ),
    "RunScenarios.cmd": (
        "Roept per scenario (bijv. BAU, Intensiveren) het RunZichtjaren.cmd script aan "
        "om de allocatie voor alle zichtjaren te draaien."
    ),
    "RunVariantData.cmd": (
        "Exporteert de VariantData voor een specifieke variant via GeoDmsRun. "
        "Wordt aangeroepen vanuit RunAll.cmd na de allocatierun."
    ),
    "RunZichtjaren.cmd": (
        "Roept de allocatie per zichtjaar aan voor een gegeven scenario/variant combinatie. "
        "Afhankelijk van de AlleenEindjaar-vlag worden tussenjaren (2030, 2040) overgeslagen."
    ),
    "run_profile.bat": (
        "Installeert de benodigde Python-packages (psutil, bokeh) en start "
        "het GeoDMSPerformance.py profilerings-script."
    ),
    "GeoDMSPerformance.py": (
        "Meet en vergelijkt de rekenprestaties van GeoDMS-runs. Voert experimenten uit, "
        "slaat resultaten op (pickle) en genereert interactieve Bokeh-grafieken voor analyse "
        "van performance-verschillen tussen configuraties."
    ),
}

SKIP_FILES = {"update_headers.py"}


# ─── Encoding ────────────────────────────────────────────────────────────────

def read_file(filepath: Path) -> str:
    """Lees bestand; probeer UTF-8 eerst, dan cp1252."""
    raw = filepath.read_bytes()
    # Verwijder BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    # Normaliseer CRLF → LF
    raw = raw.replace(b"\r\n", b"\n")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        # cp1252 (Windows-1252) voor bestanden met é, ë, ü, ij etc.
        return raw.decode("cp1252")


# ─── Tekst hulpfuncties ───────────────────────────────────────────────────────

def normalize_str(text: str) -> str:
    """Collaps whitespace in een string naar één spatie (voor multi-line Descr)."""
    return re.sub(r"\s+", " ", text).strip()


def wrap_description_dms(text: str) -> str:
    """
    Breek een lange beschrijving af op WRAP_WIDTH tekens.
    Elke regel krijgt '// ' als prefix.
    """
    lines = textwrap.wrap(text, width=WRAP_WIDTH)
    return "\n".join(f"// {l}" for l in lines)


def wrap_description_cmd(text: str) -> str:
    lines = textwrap.wrap(text, width=WRAP_WIDTH)
    return "\n".join(f"REM {l}" for l in lines)


def wrap_description_py(text: str) -> str:
    lines = textwrap.wrap(text, width=WRAP_WIDTH)
    return "\n".join(f"# {l}" for l in lines)


def has_rso_header(content: str) -> bool:
    return "RSOpen, de open source versie" in content[:3000]


# ─── Beschrijving genereren ──────────────────────────────────────────────────

def generate_dms_description(content: str, filepath: Path) -> str:
    """
    Genereer een beschrijving van een DMS-bestand o.b.v. de inhoud:
    alle Descr-waarden + #include-bestanden + container/Template-namen.
    """
    # 1. Verzamel alle Descr-waarden (multi-line → single line)
    all_descrs = []
    for m in re.finditer(r'Descr\s*=\s*"([^"]*)"', content, re.DOTALL):
        d = normalize_str(m.group(1))
        if d and d not in all_descrs:
            all_descrs.append(d)

    # 2. #include-bestanden
    includes = re.findall(r"#include\s*<([^>]+\.dms)>", content)
    includes += re.findall(r'#include\s*"([^"]+\.dms)"', content)
    include_stems = [Path(i).stem for i in includes[:8]]

    # 3. Top-level item-naam en sub-items als fallback
    top_match = re.search(r"^\s*(container|Template|unit)\s+(\w+)", content, re.MULTILINE)
    top_name = top_match.group(2) if top_match else filepath.stem
    sub_names = re.findall(r"^\t(container|Template|unit)\s+(\w+)", content[:12000], re.MULTILINE)
    sub_names += re.findall(r"^    (container|Template|unit)\s+(\w+)", content[:12000], re.MULTILINE)
    sub_names = [name for _, name in sub_names[:8]]

    parts = []

    if all_descrs:
        parts.append(all_descrs[0])
        # Voeg extra Descr-zinnen toe als ze substantieel anders zijn
        for extra in all_descrs[1:3]:
            if len(extra) > 20 and extra[:30] not in parts[0]:
                parts.append(extra)

    if include_stems:
        parts.append(f"Laadt via #include: {', '.join(include_stems)}.")
    elif sub_names and not all_descrs:
        parts.append(f"Bevat de sub-items: {', '.join(sub_names)}.")

    if not parts:
        if sub_names:
            parts.append(
                f"Specificeert de container '{top_name}', met o.a.: {', '.join(sub_names)}."
            )
        else:
            parts.append(f"Specificeert de container '{top_name}'.")

    return " ".join(parts)


# ─── Header builders ─────────────────────────────────────────────────────────

def build_dms_header(description: str) -> str:
    desc_block = wrap_description_dms(description)
    return (
        f"{DMS_DIVIDER}\n"
        "//\n"
        "// Dit is RSOpen, de open source versie van het model RuimteScanner."
        " Het scipt wordt uitgegeven onder GNU-GPL licentie.\n"
        "//\n"
        "// RSOpen is ontwikkeld door PBL Planbureau voor de Leefomgeving,"
        " i.s.m Object Vision en VU Vrije Universiteit Amsterdam.\n"
        + NEW_CONTACT_LINES
        + "//\n"
        + desc_block + "\n"
        + "//\n"
        f"{DMS_DIVIDER}\n"
    )


def build_cmd_header(description: str) -> str:
    desc_block = wrap_description_cmd(description)
    return (
        "REM ================================================================================\n"
        "REM\n"
        "REM Dit is RSOpen, de open source versie van het model RuimteScanner.\n"
        "REM Het script wordt uitgegeven onder GNU-GPL licentie.\n"
        "REM\n"
        "REM RSOpen is ontwikkeld door PBL Planbureau voor de Leefomgeving,\n"
        "REM i.s.m Object Vision en VU Vrije Universiteit Amsterdam.\n"
        "REM Opdrachtgever/ontwikkelaar PBL: Bas van Bemmel (Bas.vanBemmel@pbl.nl)\n"
        "REM Contactpersoon/ontwikkelaar Object Vision: Jip Claassens (jclaassens@objectvision.nl)\n"
        "REM Contactpersoon/ontwikkelaar Deltares: Bart Rijken (bart.rijken@deltares.nl)\n"
        "REM\n"
        + desc_block + "\n"
        + "REM\n"
        "REM ================================================================================\n"
    )


def build_py_header(description: str) -> str:
    desc_block = wrap_description_py(description)
    return (
        "# ================================================================================\n"
        "#\n"
        "# Dit is RSOpen, de open source versie van het model RuimteScanner.\n"
        "# Het script wordt uitgegeven onder GNU-GPL licentie.\n"
        "#\n"
        "# RSOpen is ontwikkeld door PBL Planbureau voor de Leefomgeving,\n"
        "# i.s.m Object Vision en VU Vrije Universiteit Amsterdam.\n"
        "# Opdrachtgever/ontwikkelaar PBL: Bas van Bemmel (Bas.vanBemmel@pbl.nl)\n"
        "# Contactpersoon/ontwikkelaar Object Vision: Jip Claassens (jclaassens@objectvision.nl)\n"
        "# Contactpersoon/ontwikkelaar Deltares: Bart Rijken (bart.rijken@deltares.nl)\n"
        "#\n"
        + desc_block + "\n"
        + "#\n"
        "# ================================================================================\n"
    )


# ─── Bestandsverwerking ──────────────────────────────────────────────────────

def update_existing_dms_header(content: str) -> str:
    """
    Werk een bestaande DMS-header bij:
    - 'Object Vision B.V.' → 'Object Vision'
    - Drie contactregels vervangen (tolereert typfouten)
    - Beschrijving NIET aanpassen
    """
    content = content.replace("Object Vision B.V.", "Object Vision")
    contact_pattern = (
        r"// Opdrachtgever/ontwikkelaar PBL:[^\n]*\n"
        r"// Contactpersoon/ontwikkelaar Object Vision[^:\n]*:[^\n]*\n"
        r"// Contac[tp]ersoon PBL:[^\n]*\n?"
    )
    content = re.sub(contact_pattern, NEW_CONTACT_LINES, content)
    return content


def process_dms(filepath: Path, content: str) -> str:
    if has_rso_header(content):
        return update_existing_dms_header(content)
    desc = generate_dms_description(content, filepath)
    return build_dms_header(desc) + "\n" + content.lstrip("\n")


def process_cmd_bat(filepath: Path, content: str) -> str:
    if has_rso_header(content):
        return content
    desc = KNOWN_DESCRIPTIONS.get(filepath.name, f"Batch-script voor RSopen: {filepath.stem}.")
    return build_cmd_header(desc) + "\n" + content.lstrip("\n")


def process_py(filepath: Path, content: str) -> str:
    if has_rso_header(content):
        return content
    desc = KNOWN_DESCRIPTIONS.get(filepath.name, f"Python-script voor RSopen: {filepath.stem}.")
    return build_py_header(desc) + "\n" + content.lstrip("\n")


def process_file(filepath: Path) -> bool:
    if filepath.name in SKIP_FILES:
        return False

    try:
        content = read_file(filepath)
    except Exception as e:
        print(f"  LEESFOUT   : {e}")
        return False

    ext = filepath.suffix.lower()
    if ext == ".dms":
        new_content = process_dms(filepath, content)
    elif ext in (".cmd", ".bat"):
        new_content = process_cmd_bat(filepath, content)
    elif ext == ".py":
        new_content = process_py(filepath, content)
    else:
        return False

    if new_content == content:
        return False

    try:
        filepath.write_text(new_content, encoding="utf-8")
    except Exception as e:
        print(f"  SCHRIJFFOUT: {e}")
        return False

    return True


# ─── Hoofdprogramma ──────────────────────────────────────────────────────────

def main():
    extensions = {".dms", ".cmd", ".bat", ".py"}
    updated, unchanged, errors = 0, 0, 0

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        for filename in sorted(filenames):
            p = Path(dirpath) / filename
            if p.suffix.lower() not in extensions:
                continue

            rel = p.relative_to(ROOT)
            try:
                changed = process_file(p)
                if changed:
                    updated += 1
                    print(f"  BIJGEWERKT : {rel}")
                else:
                    unchanged += 1
            except Exception as e:
                errors += 1
                print(f"  FOUT       : {rel}  →  {e}")

    print(f"\nKlaar: {updated} bijgewerkt, {unchanged} ongewijzigd, {errors} fouten")


if __name__ == "__main__":
    main()
