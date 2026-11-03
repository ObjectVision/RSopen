"""Brengt cfg/main/VariantParameters/VariantK.dms terug tot de twee varianten van veenweide: BAU en WBS.

Gebruik bij een merge vanuit NL2120 naar dgwb-veenweide: neem eerst de NL2120-versie van het bestand
(git checkout --theirs) en draai daarna dit script vanuit de repo-root:

    python batch/VariantK_Veenweide.py

BAU is de eerste kolom van NL2120 (BAU). WBS is diezelfde kolom met de afwijkingen in WBS hieronder: de instellingen waarop
WBS in de veenweidetak van februari 2026 van BAU afweek en die in NL2120 nog bestaan. Per parameterrij blijven zo twee waarden
over, zowel in de [ ... ]-lijsten als in de union_data(., ...)-aanroepen; NrOfRows wordt 2. Descr-teksten blijven ongemoeid, op
de zinnen in DESCR na, die in veenweide niet meer kloppen.
Regeleinden blijven zoals ze zijn. Het script is idempotent: op een bestand met twee kolommen verandert het niets.
"""
import re
from pathlib import Path

PAD = Path(__file__).resolve().parent.parent / 'cfg' / 'main' / 'VariantParameters' / 'VariantK.dms'

# De afwijkingen van WBS ten opzichte van BAU. In februari stonden er twintig; wat NL2120 niet meer kent, staat onderaan als
# commentaar met de reden, zodat het bij een nieuwe levering van Deltares terug kan.
WBS = {
    'name':                                          "'WBS'",
    'HoogbouwToegestaanInZeerMooiLandschap':         'TRUE',
    'VerhardingTovDefault':                          '0.75',
    'GeenSlooptotLeeftijd_BuitenHardePlancapaciteit': '30',
    'NietBouwenInNatura2000Buffer':                  'TRUE',
    'NietBouwenWaarSlap':                            'TRUE',
    'NietBouwenWaarNat':                             'TRUE',
    'NietBouwenWaarZettingsgevoelig':                'TRUE',
    # Drooglegging en infiltratie zoals in #501 voor WBS in DGWB-Veen afgesproken, gelijk aan BAU2 in NL2120: 40 cm in zomer en
    # winter met AWIS. In februari stond hier 20 cm in de zomer met het winterpeil aan maaiveld, en dat keurde Deltares in #501 af.
    'WinterdroogleggingK_ref':                       "'_0'",
    'ZomerdroogleggingK_ref':                        "'_0_4'",
    'InfiltratieMaatregelK_ref':                     "'AWIS'",
    # De grondwaterstanden voor de opbrengstderving: de levering WBS, de BAU-stand met de vaste stand van veenbouwsteen 1 op de
    # percelen die WBS vernat (SourceData/Water/Grondwaterstanden/WBS), totdat Deltares grondwaterstanden bij vernatting levert.
    'Hydrologie_Levering':                           "'WBS'",
    'ReserverenVoorRivierAfvoer_ref':                "'Transformatief'",  # in februari 'Ruim'; in NL2120 heet die keuze Transformatief
    'EvidentBenutVariant_Wonen':                     "'Transformeren'",   # in februari 'WBS', dat in EvidentBenut gelijk was aan Transformeren
    'EvidentBenutVariant_Werken':                    "'Transformeren'",
    'EvidentBenutVariant_Verblijfsrecreatie':        "'Transformeren'",
}
# Niet meer te zetten in NL2120, zie het issue over de gaten in veenweide:
#   Trede_Variant 'WBS': de werkentrede van WBS leunde op de eigendomslaag, die NL2120 heeft geschrapt (#874)
#   Claim_agrarisch_Variant 'claims_ggvee_minfractie': verdwenen met het voedermodel (#780)
#   MaatregelKanAangepastBouwenZijn, Waterbeheeroptie, RVF_beleidsscenario: uit NL2120 verwijderd
LABEL_WBS = "'WaterEnBodemSturend'"

# Descr-zinnen van NL2120 die in veenweide niet meer kloppen, met wat er in de plaats komt.
DESCR = [
    ('en NbSGenuanceerd) en SourceData/Water/Grondwaterstanden kent dezelfde drie plus de referentie van het basisjaar.',
     'en NbSGenuanceerd, in veenweide ook WBS) en SourceData/Water/Grondwaterstanden kent dezelfde vier plus de referentie van het basisjaar.'),
]


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


def twee(bau, wbs):
    """Twee cellen in de kolombreedte van de eerste cel, zodat de tabel leesbaar blijft."""
    breedte = len(bau)
    return bau.rstrip().ljust(breedte) + ',' + (' ' + wbs.strip()).ljust(breedte)


def verwerk(tekst):
    eol = '\r\n' if '\r\n' in tekst else '\n'
    uit, sla_alinea_over = [], False
    for r in tekst.split(eol):
        if r.startswith('// BAU EN BAU2:'):
            sla_alinea_over = True
            uit += ['// BAU EN WBS:',
                    '//   Veenweide vergelijkt per peilgebied BAU en WBS (waterbodemsturend, PostAllocAnalyses/Landbouw/PeilOptimalisatie). BAU is de',
                    '//   BAU van NL2120; WBS wijkt af in de bouwbeperkingen op natte, slappe en zettingsgevoelige grond, de drooglegging en de',
                    '//   infiltratiemaatregel (#501), de grondwaterstanden voor de opbrengstderving, de reservering voor rivierafvoer en evident',
                    '//   benut. Deze tabel komt uit batch/VariantK_Veenweide.py, toegepast op de tabel van NL2120.',
                    '//']
            continue
        if sla_alinea_over:
            if r.startswith('////'):
                sla_alinea_over = False
                uit.append(r)
            continue
        r = re.sub(r'(unit<UInt8> VariantK: NrOfRows = )\d+', r'\g<1>2', r)
        for oud, nieuw in DESCR:
            r = r.replace(oud, nieuw)
        m = re.match(r'^\s*attribute<[^>]+>\s*(\w+)\s*:\s*\[', r)
        if m:
            i = m.end() - 1
            j = find_matching(r, i, '[', ']')
            items = split_top(r[i + 1:j])
            if len(items) != 2:
                r = r[:i + 1] + twee(items[0], WBS.get(m.group(1), items[0])) + r[j:]
        elif 'union_data' in r and re.match(r'^\s*attribute<', r):
            naam = re.match(r'^\s*attribute<[^>]+>\s*(\w+)', r).group(1)
            i = r.index('(', r.index('union_data'))
            j = find_matching(r, i, '(', ')')
            items = split_top(r[i + 1:j])
            if len(items) != 3:
                tweede = LABEL_WBS if naam == 'Label' else WBS.get(naam, items[1])
                r = r[:i + 1] + items[0] + ',' + twee(items[1], tweede) + r[j:]
        kop = re.search(r'//\s*BusinessAsUsual\s*,', r)
        if kop and re.search(r'BusinessAsUsual2|NbS', r[kop.end():]):
            r = r[:kop.end()] + ' WaterEnBodemSturend'
        uit.append(r)
    return eol.join(uit)


def main():
    oud = PAD.read_text(encoding='utf-8', newline='')
    nieuw = verwerk(oud)
    if nieuw == oud:
        print('VariantK.dms had al de twee kolommen van veenweide; niets veranderd.')
        return
    PAD.write_text(nieuw, encoding='utf-8', newline='')
    print(f'VariantK.dms teruggebracht tot BAU en WBS ({len(oud.splitlines())} regels).')


if __name__ == '__main__':
    main()
