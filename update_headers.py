#!/usr/bin/env python3
"""Update RSOpen file headers: contact info en beschrijvingen.

- Bestaande headers: contact info bijwerken + beschrijving verbeteren
- Bestanden zonder header: volledige header toevoegen met gegenereerde beschrijving
"""

import os
import re
from pathlib import Path

ROOT = Path(r"C:\ProjDir\RSopen\.claude\worktrees\exciting-mcnulty")

DMS_DIVIDER = "/" * 296

# Nieuwe contactregels
NEW_CONTACT_LINES = (
    "// Opdrachtgever/ontwikkelaar PBL: Bas van Bemmel (Bas.vanBemmel@pbl.nl)\n"
    "// Contactpersoon/ontwikkelaar Object Vision: Jip Claassens (jclaassens@objectvision.nl)\n"
    "// Contactpersoon/ontwikkelaar Deltares: Bart Rijken (bart.rijken@deltares.nl)\n"
)

# Handmatige beschrijvingen voor niet-DMS bestanden
KNOWN_DESCRIPTIONS = {
    "RunAll.cmd": (
        "Dit script start een volledige RSopen modelrun. Het stelt de benodigde parameters in "
        "(paden, GeoDMS versie), vraagt de gebruiker of basedata hergebruikt kan worden en of "
        "alleen het eindjaar berekend moet worden, en roept daarna de deelscripts aan."
    ),
    "RunImpl.cmd": (
        "Dit script is de generieke wrapper voor het aanroepen van GeoDmsRun.exe met een opgegeven "
        "DMS-container. Het legt de starttijd vast, voert de berekening uit en logt de resultaten."
    ),
    "RunScenarios.cmd": (
        "Dit script roept per scenario (bijv. BAU, Intensiveren) het RunZichtjaren.cmd script aan "
        "om de allocatie voor alle zichtjaren te draaien."
    ),
    "RunVariantData.cmd": (
        "Dit script exporteert de VariantData voor een specifieke variant via GeoDmsRun. "
        "Het wordt aangeroepen vanuit RunAll.cmd na de allocatie."
    ),
    "RunZichtjaren.cmd": (
        "Dit script roept de allocatie per zichtjaar aan voor een gegeven scenario/variant combinatie. "
        "Afhankelijk van de AlleenEindjaar-vlag worden tussenjaren (2030, 2040) overgeslagen."
    ),
    "run_profile.bat": (
        "Dit script installeert de benodigde Python-packages (psutil, bokeh) en start vervolgens "
        "het GeoDMSPerformance.py profilerings-script."
    ),
    "GeoDMSPerformance.py": (
        "Dit script meet en vergelijkt de rekenprestaties van GeoDMS-runs. Het voert experimenten "
        "uit, slaat resultaten op (pickle), en genereert interactieve Bokeh-grafieken voor analyse "
        "van performance-verschillen tussen configuraties."
    ),
}

# Bestanden die niet verwerkt worden (utility scripts)
SKIP_FILES = {"update_headers.py"}


# ─── Hulpfuncties ────────────────────────────────────────────────────────────

def has_rso_header(content: str) -> bool:
    """Check of het bestand al een RSopen-header heeft (elk comment-stijl).

    Gebruikt een specifiekere zoekstring om false positives te vermijden
    (bijv. 'RSopen' als bestandspad in code).
    """
    stripped = content.lstrip("\ufeff")  # BOM
    return "RSOpen, de open source versie" in stripped[:3000]


def extract_top_container_descr(content: str) -> str | None:
    """
    Geeft de Descr van de TOP-LEVEL container-declaratie terug, of None.
    Kijkt alleen in de declaratie vóór de eerste '{' om sub-container Descr's
    te vermijden.
    """
    container_match = re.search(r'^\s*container\s+\w+', content, re.MULTILINE)
    if not container_match:
        return None

    start = container_match.start()
    # Neem het blok van de declaratie t/m de eerste '{' (max 600 tekens)
    decl_block = content[start: start + 600]
    brace_pos = decl_block.find('{')
    if brace_pos != -1:
        decl_block = decl_block[:brace_pos]

    m = re.search(r'Descr\s*=\s*"([^"]+)"', decl_block)
    return m.group(1).strip() if m else None


def extract_dms_description(content: str, filepath: Path) -> str:
    """
    Probeer een zinvolle beschrijving uit de DMS-bestandsinhoud te extraheren.
    Volgorde:
      1. Descr-attribuut op de TOP-LEVEL container (vóór eerste '{')
      2. Container-naam + directe sub-container namen
      3. Bestandsnaam als fallback
    """
    descr = extract_top_container_descr(content)
    if descr:
        return descr

    container_match = re.search(r'^\s*container\s+(\w+)', content, re.MULTILINE)
    if container_match:
        top = container_match.group(1)
        sub_containers = re.findall(
            r'^\s{1,4}container\s+(\w+)', content[:6000], re.MULTILINE
        )[:5]
        if sub_containers:
            subs = ", ".join(sub_containers)
            return f"Deze file specificeert de container '{top}', met o.a.: {subs}."
        return f"Deze file specificeert de container '{top}'."

    return f"Deze file bevat configuratie voor '{filepath.stem}'."


# ─── Header builders ─────────────────────────────────────────────────────────

def build_dms_header(description: str) -> str:
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
        f"// {description}\n"
        "//\n"
        f"{DMS_DIVIDER}\n"
    )


def build_cmd_header(description: str) -> str:
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
        f"REM {description}\n"
        "REM\n"
        "REM ================================================================================\n"
    )


def build_py_header(description: str) -> str:
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
        f"# {description}\n"
        "#\n"
        "# ================================================================================\n"
    )


# ─── Bestandsverwerking ──────────────────────────────────────────────────────

def update_existing_dms_header(content: str, filepath: Path) -> str:
    """
    Werk een bestaande DMS-header bij:
    - Object Vision B.V. → Object Vision
    - Contactregels vervangen
    - Beschrijving bijwerken alleen als de top-container een Descr-attribuut heeft
    """
    content = content.replace("Object Vision B.V.", "Object Vision")

    contact_pattern = (
        r"// Opdrachtgever/ontwikkelaar PBL:[^\n]*\n"
        r"// Contactpersoon/ontwikkelaar Object Vision[^:\n]*:[^\n]*\n"
        r"// Contac[tp]ersoon PBL:[^\n]*\n?"
    )
    content = re.sub(contact_pattern, NEW_CONTACT_LINES, content)

    top_descr = extract_top_container_descr(content)
    if top_descr:
        desc_block_pattern = (
            r"(// Contactpersoon/ontwikkelaar Deltares:[^\n]*\n"
            r"//\n)"
            r"((?://[^\n]*\n)+)"
            r"(//\n"
            r"/{100,})"
        )
        content = re.sub(
            desc_block_pattern,
            r"\g<1>" + f"// {top_descr}\n" + r"\g<3>",
            content,
            count=1,
        )

    return content


def process_dms(filepath: Path, content: str) -> str:
    if has_rso_header(content):
        return update_existing_dms_header(content, filepath)
    desc = extract_dms_description(content, filepath)
    return build_dms_header(desc) + "\n" + content.lstrip("\n")


def process_cmd_bat(filepath: Path, content: str) -> str:
    if has_rso_header(content):
        return content  # al bijgewerkt; CMD-headers worden niet verder gewijzigd
    desc = KNOWN_DESCRIPTIONS.get(filepath.name, f"Batch-script voor RSopen: {filepath.stem}.")
    return build_cmd_header(desc) + "\n" + content.lstrip("\n")


def process_py(filepath: Path, content: str) -> str:
    if has_rso_header(content):
        return content
    desc = KNOWN_DESCRIPTIONS.get(filepath.name, f"Python-script voor RSopen: {filepath.stem}.")
    return build_py_header(desc) + "\n" + content.lstrip("\n")


def process_file(filepath: Path) -> bool:
    """Verwerk één bestand. Geeft True als het bestand is gewijzigd."""
    if filepath.name in SKIP_FILES:
        return False

    try:
        raw = filepath.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            content = raw[3:].decode("utf-8", errors="replace")
            bom = "\ufeff"
        else:
            content = raw.decode("utf-8", errors="replace")
            bom = ""
    except Exception as e:
        print(f"  LEESFOUT: {e}")
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
        filepath.write_text(bom + new_content, encoding="utf-8")
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
