"""Zet een csv om naar parquet zonder inhoudelijke bewerking en toetst daarna of de parquet waarde voor waarde gelijk is aan de csv.

RSopen leest een grote tabel die elk proces nodig heeft liever als parquet, zoals de LISA-punten in WritePrivData/LISA/Read: een parquet
leest alleen de gebruikte kolommen en kent zijn aantal rijen, een csv moet bij elke lezing helemaal worden doorlopen.

De parquet heeft dezelfde rijen, kolommen en kolomnamen als de csv, alleen getypeerd. Het type volgt per kolom uit het hele bestand:
- een kolom die in de csv tussen aanhalingstekens staat blijft tekst, zodat codes als sbi08 of een postcode hun voorloopnullen houden;
- een kolom met alleen gehele getallen zonder voorloopnul wordt int32, of int64 als dat niet past;
- een kolom met alleen getallen met een punt als decimaalteken en zonder voorloopnul wordt float64;
- al het andere blijft tekst. Een lege waarde wordt null.
Scheidingsteken (; of ,) en een BOM voor de kop worden herkend. Naam, omvang en sha256 van de csv staan in de metadata van de parquet.
Het script schrijft eerst <parquet>.deel en geeft pas de echte naam als de toets geen enkele afwijking vindt; een bestaande parquet
wordt nooit overschreven.

Nodig: Python 3 met pyarrow (python -m pip install --user pyarrow).
Gebruik: python batch/csv_naar_parquet.py <csv> <parquet>
"""
import hashlib, os, sys, time
import pyarrow as pa, pyarrow.csv as pc, pyarrow.compute as pcp, pyarrow.parquet as pq

GEHEEL = r'^-?(0|[1-9][0-9]*)$'
GETAL = r'^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$'
VOORLOOPNUL = r'^[-+]?0[0-9]'
PROEFREGELS = 20000


def lees_als_tekst(src, sep, kop):
    t = pc.read_csv(src, read_options=pc.ReadOptions(block_size=1 << 26, encoding='utf8'),
                    parse_options=pc.ParseOptions(delimiter=sep),
                    convert_options=pc.ConvertOptions(column_types={k: pa.string() for k in kop}, strings_can_be_null=False))
    namen = [n.lstrip('﻿') for n in t.column_names]
    if namen != kop:
        sys.exit(f'kolommen wijken af van de kop: {namen} tegen {kop}')
    return t.rename_columns(kop)


def leeg_naar_null(a):
    return pcp.if_else(pcp.equal(a, ''), pa.scalar(None, pa.string()), a)


def typeer(a, tussen_aanhalingstekens):
    gevuld = pcp.filter(a, pcp.not_equal(a, ''))
    a = leeg_naar_null(a)
    if tussen_aanhalingstekens or len(gevuld) == 0:
        return a
    if pcp.all(pcp.match_substring_regex(gevuld, GEHEEL)).as_py():
        a64 = pcp.cast(a, pa.int64())
        past = -2**31 <= pcp.min(a64).as_py() and pcp.max(a64).as_py() < 2**31
        return pcp.cast(a64, pa.int32()) if past else a64
    if pcp.all(pcp.match_substring_regex(gevuld, GETAL)).as_py() and not pcp.any(pcp.match_substring_regex(gevuld, VOORLOOPNUL)).as_py():
        return pcp.cast(a, pa.float64())
    return a


def afwijkend(tekst, waarde):
    """Aantal rijen waar de parquetwaarde niet gelijk is aan de csv-tekst: gehele getallen en tekst letterlijk, kommagetallen als getal."""
    tekst = leeg_naar_null(tekst)
    if pa.types.is_floating(waarde.type):
        tekst = pcp.cast(tekst, waarde.type)
    elif not pa.types.is_string(waarde.type):
        waarde = pcp.cast(waarde, pa.string())
    gelijk = pcp.and_(pcp.equal(pcp.is_null(tekst), pcp.is_null(waarde)), pcp.fill_null(pcp.equal(tekst, waarde), True))
    return len(gelijk) - pcp.sum(gelijk).as_py()


def main(src, dst):
    if os.path.exists(dst):
        sys.exit(f'{dst} bestaat al; het script overschrijft geen bestaande parquet')
    t0 = time.time()
    with open(src, 'rb') as f:
        kopregel = f.readline().decode('utf-8-sig').rstrip('\r\n')
    sep = ';' if kopregel.count(';') > kopregel.count(',') else ','
    kop = kopregel.split(sep)

    # Kolommen tussen aanhalingstekens, uit de eerste regels zonder scheidingsteken binnen een veld.
    tekstkolommen = set()
    with open(src, encoding='utf-8-sig') as f:
        next(f)
        for i, regel in enumerate(f):
            if i >= PROEFREGELS:
                break
            velden = regel.rstrip('\r\n').split(sep)
            if len(velden) == len(kop):
                tekstkolommen.update(k for k, v in zip(kop, velden) if v.startswith('"'))

    t = lees_als_tekst(src, sep, kop)
    kolommen = [typeer(t[k], k in tekstkolommen) for k in kop]

    h = hashlib.sha256()
    with open(src, 'rb') as f:
        for blok in iter(lambda: f.read(1 << 24), b''):
            h.update(blok)
    meta = {'bron': os.path.basename(src), 'bron_omvang': str(os.path.getsize(src)), 'bron_sha256': h.hexdigest(),
            'omgezet': time.strftime('%Y-%m-%d'), 'werkwijze': 'batch/csv_naar_parquet.py van RSopen, zonder inhoudelijke bewerking'}
    deel = dst + '.deel'
    pq.write_table(pa.table(kolommen, names=kop).replace_schema_metadata(meta), deel, compression='snappy', row_group_size=1 << 20)

    p = pq.read_table(deel)
    fouten = 0 if p.num_rows == t.num_rows and p.column_names == kop else 1
    for k in kop:
        n = afwijkend(t[k], p[k])
        fouten += n
        print(f'  {k:24s} {str(p[k].type):8s} {"tussen aanhalingstekens" if k in tekstkolommen else "":24s} afwijkend {n}')
    if fouten:
        sys.exit(f'{fouten} afwijkingen tussen csv en parquet; {deel} blijft staan om te onderzoeken')
    os.replace(deel, dst)
    print(f'{os.path.basename(src)}: {p.num_rows:,} rijen, {len(kop)} kolommen, scheidingsteken {sep!r}, geen afwijkingen; '
          f'{os.path.getsize(src):,} bytes csv naar {os.path.getsize(dst):,} bytes parquet in {time.time() - t0:.1f} s')
    print(f'sha256 csv {meta["bron_sha256"]}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
