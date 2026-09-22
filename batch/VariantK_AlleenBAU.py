"""Brengt cfg/main/VariantParameters/VariantK.dms terug tot de eerste kolom (BAU).

Gebruik bij een merge vanuit NL2120 naar main: neem eerst de NL2120-versie van het bestand
(git checkout --theirs) en draai daarna dit script vanuit de repo-root:

    python batch/VariantK_AlleenBAU.py

Het script laat per parameterrij alleen de eerste waarde staan, zowel in de [ ... ]-lijsten als
in de union_data(., ...)-aanroepen, zet NrOfRows op 1, kort de kolomkopjes in de commentaren in en
haalt de alinea over BAU en BAU2 uit de kop. Descr-teksten blijven ongemoeid. Regeleinden (LF of
CRLF) blijven zoals ze zijn. Het script is idempotent: op een bestand met een kolom verandert het niets.
"""
import re
from pathlib import Path

PAD = Path(__file__).resolve().parent.parent / 'cfg' / 'main' / 'VariantParameters' / 'VariantK.dms'


def split_top(s):
    """Splitst op komma's buiten aanhalingstekens en buiten haakjes."""
    items, cur, quoted, depth = [], '', False, 0
    for ch in s:
        if ch == "'":
            quoted = not quoted
        if not quoted:
            if ch in '([':
                depth += 1
            elif ch in ')]':
                depth -= 1
        if ch == ',' and not quoted and depth == 0:
            items.append(cur)
            cur = ''
        else:
            cur += ch
    items.append(cur)
    return items


def find_matching(s, i, open_ch, close_ch):
    depth, quoted = 0, False
    for j in range(i, len(s)):
        ch = s[j]
        if ch == "'":
            quoted = not quoted
        if quoted:
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return j
    raise ValueError(f'geen sluithaakje gevonden in: {s[:80]}')


def verwerk(tekst):
    eol = '\r\n' if '\r\n' in tekst else '\n'
    regels = tekst.split(eol)
    uit, sla_alinea_over = [], False
    for r in regels:
        if r.startswith('// BAU EN BAU2:'):
            sla_alinea_over = True
            continue
        if sla_alinea_over:
            if r.startswith('////'):
                sla_alinea_over = False
                uit.append(r)
            continue
        r = re.sub(r'(unit<UInt8> VariantK: NrOfRows = )\d+', r'\g<1>1', r)
        m = re.match(r'^\s*attribute<[^>]+>\s*\w+\s*:\s*\[', r)
        if m:
            i = m.end() - 1
            j = find_matching(r, i, '[', ']')
            r = r[:i + 1] + split_top(r[i + 1:j])[0].rstrip() + r[j:]
        elif 'union_data' in r and re.match(r'^\s*attribute<', r):
            i = r.index('(', r.index('union_data'))
            j = find_matching(r, i, '(', ')')
            items = split_top(r[i + 1:j])
            r = r[:i + 1] + items[0] + ',' + items[1].rstrip() + r[j:]
        kop = re.search(r'//\s*(BusinessAsUsual|BAU)\s*,', r)
        if kop and re.search(r'BAU2|NbS', r[kop.end():]):
            r = r[:kop.end() - 1].rstrip()
        uit.append(r)
    res = eol.join(uit)
    return res.replace('zie het kopje BAU EN BAU2 bovenaan dit bestand',
                       'zie het kopje BAU EN BAU2 bovenaan de NL2120-versie van dit bestand')


def main():
    oud = PAD.read_text(encoding='utf-8', newline='')
    nieuw = verwerk(oud)
    if nieuw == oud:
        print('VariantK.dms had al een kolom; niets veranderd.')
        return
    PAD.write_text(nieuw, encoding='utf-8', newline='')
    print(f'VariantK.dms teruggebracht tot de BAU-kolom ({len(oud.splitlines())} -> {len(nieuw.splitlines())} regels).')


if __name__ == '__main__':
    main()
