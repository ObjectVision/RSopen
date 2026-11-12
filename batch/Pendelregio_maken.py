"""Maakt de indeling van Nederland in pendelregio's op gemeenten (#392) en schrijft hem naar data/Pendelregio/Pendelregio_gemeente.csv.

De indeling volgt de methode voor functional urban areas (FUA) van de Europese Commissie, het JRC en de OECD:
1. Een stedelijk centrum is een aaneengesloten gebied van vierkanten van 1 km (4-buren) met minstens DICHT inwoners per km2, samen
   minstens CENTRUM_MIN inwoners. De stap waarin de officiele methode gaten in een centrum opvult, zit er niet in.
2. Een stad is de gemeente met minstens AANDEEL_STAD van haar inwoners in een centrum; heeft een centrum er geen, dan de gemeente met
   de meeste inwoners in dat centrum. Stuurt een stad minstens PENDEL_DREMPEL van haar werkende inwoners naar een andere stad, dan
   horen ze bij elkaar; dat wordt per paar van oorspronkelijke steden bepaald, en ketens van zulke paren worden een stad. Met
   --samenvoegen eigen (de standaard) gaat een stad met een eigen pendelzone niet op in een andere stad: Hoorn, waar West-Friesland
   op leunt, blijft dan los van Amsterdam. Een eigen pendelzone is minstens een gemeente die volgens stap 3 bij deze stad alleen hoort.
3. Een gemeente hoort bij de stad waar het grootste deel van haar werkende inwoners werkt, als dat minstens PENDEL_DREMPEL is.
   Ingesloten gemeenten komen erbij, losliggende gaan eruit.
Drie stappen zijn eigen toevoegingen:
4. Een FUA blijft binnen GRENS (standaard de provincie), omdat de overloop van de allocatie de restclaim per regio uitrekent als claim
   min stand, wat alleen klopt als een regio binnen de regio van de volgende stap valt. Een deel aan de andere kant van de grens met
   een eigen stad wordt een eigen FUA, een deel zonder stad gaat naar de rest.
5. Met --rest buur (de standaard) gaat elke gemeente buiten een FUA naar de aangrenzende regio binnen dezelfde grens waar ze de meeste
   pendel naartoe stuurt, zodat er geen restregio's overblijven. Met --rest corop vormen ze per COROP een restregio, per aaneengesloten
   stuk, en gaat een restregio met minder dan MIN_REST_WONINGEN woningen op in de regio waar hij de meeste pendel naartoe stuurt.
6. Binnen elke pendelregio is elke oorspronkelijke stad uit stap 2 een stadregio, en vormen de overige gemeenten samen het ommeland.
   Wonen alloceert eerst per stadregio, dan per pendelregio, dan per provincie.

Bronnen:
- CBS-tabel 85481NED, banen van werknemers in december van woon- naar werkgemeente, gemiddeld over JAREN, via de OData-feed van het CBS.
- De CBS-vierkantstatistiek van 100 meter van VIERKANT_JAAR, voor inwoners en woningen: <RSO_DataDir>/Actoren/Bevolking.
- De CBS-gebiedsindelingen van GEBIED_JAAR voor gemeenten, COROP en provincies: <RSO_DataDir>/RegioIndelingen.
De geopackages worden eerst naar de werkmap gekopieerd, zodat er bij het lezen niets naast de bron op de share komt. De gemeente-indeling
van de pendel moet gelijk zijn aan die van GEBIED_JAAR; het script stopt als er een code ontbreekt.

Gebruik: python batch/Pendelregio_maken.py [--rso-datadir <map>] [--werkmap <map>] [--grens provincie|corop|geen]
                                          [--samenvoegen eigen|fua] [--rest buur|corop]
"""

import argparse
import json
import os
import shutil
import sys
import urllib.parse
import urllib.request
import winreg
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import scipy.ndimage as ndi

DICHT = 1500.0              # inwoners per km2 in een stedelijk centrum (Degree of Urbanisation)
CENTRUM_MIN = 50000.0       # inwoners per stedelijk centrum
AANDEEL_STAD = 0.5          # deel van de inwoners van een gemeente in een centrum om stad te zijn
PENDEL_DREMPEL = 0.15       # deel van de werkende inwoners dat naar de stad pendelt
MIN_REST_WONINGEN = 20000   # kleinste restregio; zo is bijna geen regio kleiner dan de kleinste NVM-regio (23.587 woningen)
JAREN = [2023, 2024]        # jaren van de pendel; in deze jaren is de gemeente-indeling gelijk aan die van GEBIED_JAAR, eerdere jaren hebben gemeenten van voor een herindeling
VIERKANT_JAAR = 2024        # jaar van de vierkantstatistiek, het laatste jaar van de pendel
GEBIED_JAAR = 2024          # jaar van de gemeente-indeling, gelijk aan ModelParameters/RegioIndelingen_CBSjaar
KM = 1000.0                 # zijde van de vierkanten voor de stedelijke centra, in meter
CBS_TABEL = "85481NED"

ROOT = Path(__file__).resolve().parent.parent
UIT = ROOT / "data" / "Pendelregio" / "Pendelregio_gemeente.csv"


def register(waarde):
    sleutel = rf"SOFTWARE\ObjectVision\{os.environ['COMPUTERNAME']}\GeoDMS"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sleutel) as k:
        return winreg.QueryValueEx(k, waarde)[0]


def kopie(bron, werkmap):
    doel = werkmap / bron.name
    if not doel.exists() or doel.stat().st_size != bron.stat().st_size:
        shutil.copy2(bron, doel)
    return doel


def pendel(werkmap, codes):
    """Banen van werknemers van woon- naar werkgemeente, gemiddeld over JAREN, als matrix in de volgorde van codes."""
    cache = werkmap / f"cbs_{CBS_TABEL}_{JAREN[0]}_{JAREN[-1]}.csv"
    if not cache.exists():
        rijen = []
        for jaar in JAREN:
            filt = f"Perioden eq '{jaar}MM12' and substringof('GM', WoonregioS) and substringof('GM', WerkregioS)"
            url = f"https://opendata.cbs.nl/ODataFeed/odata/{CBS_TABEL}/TypedDataSet?$format=json&$filter=" + urllib.parse.quote(filt)
            while url:
                with urllib.request.urlopen(url, timeout=300) as r:
                    d = json.load(r)
                rijen += [(v['WoonregioS'].strip(), v['WerkregioS'].strip(), jaar, v['BanenVanWerknemers_1']) for v in d['value']]
                url = d.get('odata.nextLink')
        pd.DataFrame(rijen, columns=['woon', 'werk', 'jaar', 'banen_x1000']).to_csv(cache, index=False)
    t = pd.read_csv(cache)
    # de tabel heeft ook lege regels voor gemeenten van voor een herindeling; GM0000 is een niet in te delen gemeente
    t = t[t['banen_x1000'].notna() & (t['woon'] != 'GM0000') & (t['werk'] != 'GM0000')]
    idx = {c: i for i, c in enumerate(codes)}
    onbekend = sorted(set(t['woon']) - set(idx))
    if onbekend:
        sys.exit(f"Gemeentecodes in de pendel die niet in de gebiedsindeling van {GEBIED_JAAR} staan: {onbekend[:10]}")
    F = np.zeros((len(codes), len(codes)))
    g = t.groupby(['woon', 'werk'])['banen_x1000'].sum() * 1000 / len(JAREN)
    for (wo, we), v in g.items():
        F[idx[wo], idx[we]] = v
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rso-datadir", type=Path, default=None, help="de map RSOpen in SourceData; standaard SourceDataDir uit het register plus RSOpen")
    ap.add_argument("--werkmap", type=Path, default=None, help="map voor kopieen en de pendelcache; standaard LocalDataDir uit het register plus Pendelregio_maken")
    ap.add_argument("--grens", choices=["provincie", "corop", "geen"], default="provincie")
    ap.add_argument("--samenvoegen", choices=["eigen", "fua"], default="eigen", help="eigen: een stad met een eigen pendelzone gaat niet op in een andere stad; fua: altijd samenvoegen zoals de FUA-methode")
    ap.add_argument("--rest", choices=["buur", "corop"], default="buur", help="buur: gemeenten buiten een FUA naar de aangrenzende regio met de meeste pendel; corop: restregio's per COROP")
    a = ap.parse_args()
    rso = a.rso_datadir or Path(register("SourceDataDir")) / "RSOpen"
    werkmap = a.werkmap or Path(register("LocalDataDir")) / "Pendelregio_maken"
    werkmap.mkdir(parents=True, exist_ok=True)

    # gemeenten, COROP en provincies
    gpkg = kopie(rso / "RegioIndelingen" / f"cbsgebiedsindelingen{GEBIED_JAAR}.gpkg", werkmap)
    gm = pyogrio.read_dataframe(gpkg, layer='gemeente_gegeneraliseerd').sort_values('statcode').reset_index(drop=True)
    codes = list(gm['statcode']); naam = list(gm['statnaam']); n = len(codes)
    punt = gpd.GeoDataFrame(geometry=gm.geometry.representative_point(), crs=gm.crs)
    def binnen(laag):
        vl = pyogrio.read_dataframe(gpkg, layer=laag)[['statcode', 'statnaam', 'geometry']]
        j = gpd.sjoin(punt, vl, how='left', predicate='within')
        j = j[~j.index.duplicated()]
        return j['statcode'].to_numpy(), j['statnaam'].to_numpy()
    corop, corop_naam = binnen('coropgebied_gegeneraliseerd')
    prov, prov_naam = binnen('provincie_gegeneraliseerd')
    if pd.isna(corop).any() or pd.isna(prov).any():
        sys.exit("Niet elke gemeente valt in een COROP-gebied en een provincie.")
    corop_naam_van = dict(zip(corop, corop_naam))
    prov_naam_van = dict(zip(prov, prov_naam))
    buren = [set() for _ in range(n)]
    geb = gm.geometry.buffer(10)
    for i, g in enumerate(geb):
        buren[i] = {int(j) for j in geb.sindex.query(g, predicate='intersects') if j != i}

    # inwoners en woningen per vierkant van 100 m, naar gemeente en naar vierkant van 1 km
    vk = pyogrio.read_dataframe(kopie(rso / "Actoren" / "Bevolking" / f"cbs_vk100_{VIERKANT_JAAR}_vol.gpkg", werkmap),
                                columns=['aantal_inwoners', 'aantal_woningen'])
    for k in ['aantal_inwoners', 'aantal_woningen']:
        vk[k] = vk[k].where(vk[k] >= 0, 0)
    pt = gpd.GeoDataFrame(vk[['aantal_inwoners', 'aantal_woningen']], geometry=vk.geometry.centroid, crs=vk.crs)
    j = gpd.sjoin_nearest(pt, gm[['geometry']], how='left')
    j = j[~j.index.duplicated()]
    g_vk = j['index_right'].to_numpy()
    inw, won = vk['aantal_inwoners'].to_numpy(float), vk['aantal_woningen'].to_numpy(float)
    inw_gm = np.bincount(g_vk, weights=inw, minlength=n); won_gm = np.bincount(g_vk, weights=won, minlength=n)
    x, y = pt.geometry.x.to_numpy(), pt.geometry.y.to_numpy()
    ix, iy = np.floor(x / KM).astype(int), np.floor(y / KM).astype(int)
    ix -= ix.min(); iy -= iy.min()
    km = np.zeros((iy.max() + 1, ix.max() + 1)); np.add.at(km, (iy, ix), inw)

    # 1. stedelijke centra
    lab, nl = ndi.label(km >= DICHT)
    som = ndi.sum(km, lab, index=np.arange(1, nl + 1))
    centrum = np.zeros(nl + 1, int); geldig = np.where(som >= CENTRUM_MIN)[0] + 1
    centrum[geldig] = np.arange(1, len(geldig) + 1); nc = len(geldig)
    c_vk = centrum[lab[iy, ix]]

    # 2. steden
    ic = np.zeros((n, nc + 1)); np.add.at(ic, (g_vk, c_vk), inw)
    stad_van = np.full(n, -1)
    for c in range(1, nc + 1):
        leden = np.where(ic[:, c] / np.maximum(inw_gm, 1) >= AANDEEL_STAD)[0]
        if len(leden) == 0:
            leden = [int(np.argmax(ic[:, c]))]
        for i in leden:
            if stad_van[i] < 0:
                stad_van[i] = c
    F = pendel(werkmap, codes)
    steden = sorted(set(stad_van[stad_van >= 0]))
    Rw = F.sum(axis=1)
    eigen_zone = set()
    if a.samenvoegen == "eigen":
        for i in range(n):
            if stad_van[i] >= 0 or Rw[i] == 0:
                continue
            aandeel = {c: F[i, stad_van == c].sum() / Rw[i] for c in steden}
            c = max(aandeel, key=aandeel.get)
            if aandeel[c] >= PENDEL_DREMPEL:
                eigen_zone.add(c)
    groep = {c: c for c in steden}
    def wortel(c):
        while groep[c] != c:
            c = groep[c]
        return c
    for s1 in steden:
        if s1 in eigen_zone:
            continue
        a1 = stad_van == s1
        for s2 in steden:
            if s1 != s2 and F[np.ix_(a1, stad_van == s2)].sum() / max(F[a1].sum(), 1) >= PENDEL_DREMPEL:
                r1, r2 = wortel(s1), wortel(s2)
                if r1 != r2:
                    groep[max(r1, r2)] = min(r1, r2)
    stad = np.array([wortel(c) if c >= 0 else -1 for c in stad_van])
    fua_ids = sorted(set(stad[stad >= 0]))
    def stadnaam(f):
        leden = np.where(stad == f)[0]
        return naam[max(leden, key=lambda i: inw_gm[i])]

    # 3. pendelzones
    fua = stad.copy()
    for i in range(n):
        if fua[i] >= 0 or Rw[i] == 0:
            continue
        aandeel = {f: F[i, stad == f].sum() / Rw[i] for f in fua_ids}
        f = max(aandeel, key=aandeel.get)
        if aandeel[f] >= PENDEL_DREMPEL:
            fua[i] = f
    def componenten(leden):
        leden = set(leden); res = []
        while leden:
            s = leden.pop(); comp = {s}; rand = [s]
            while rand:
                i = rand.pop()
                for j in buren[i]:
                    if j in leden:
                        leden.remove(j); comp.add(j); rand.append(j)
            res.append(sorted(comp))
        return res
    for _ in range(3):
        for f in fua_ids:
            leden = set(np.where(fua == f)[0]); kern = set(np.where(stad == f)[0])
            for comp in componenten(leden):
                if not kern & set(comp):
                    fua[comp] = -1
        for i in range(n):
            if fua[i] < 0 and buren[i]:
                b = {fua[j] for j in buren[i]}
                if len(b) == 1 and -1 not in b:
                    fua[i] = b.pop()

    # 4 en 5. regio's binnen de grens; de gemeenten buiten een FUA naar een buurregio of in restregio's per COROP
    grens = {'provincie': prov, 'corop': corop, 'geen': np.zeros(n, int)}[a.grens]
    grens_naam = {'provincie': prov_naam_van, 'corop': corop_naam_van, 'geen': {0: 'Nederland'}}[a.grens]
    regio = np.full(n, -1); namen, soort, stadkol = [], [], []
    for f in fua_ids:
        leden = np.where(fua == f)[0]
        hoofd = grens[max(np.where(stad == f)[0], key=lambda i: inw_gm[i])]
        for g in sorted(set(grens[leden]), key=lambda g: g != hoofd):
            deel = [i for i in leden if grens[i] == g]
            eigen = [i for i in deel if stad_van[i] >= 0]
            if g == hoofd or eigen:
                regio[deel] = len(namen)
                namen.append(stadnaam(f) if g == hoofd else naam[max(eigen, key=lambda i: inw_gm[i])]); soort.append('FUA')
    rest = np.where(regio < 0)[0]
    if a.rest == "buur":
        # per ronde gaat elke gemeente met een buur die al een regio heeft naar de buurregio waar ze de meeste pendel naartoe stuurt; een
        # gemeente zonder zo'n buur wacht een ronde. Wat aan geen enkele regio grenst, gaat naar de regio binnen de grens met de meeste
        # pendel, en is er binnen de grens geen regio (een provincie zonder stad), dan vormt het een restregio voor die grens.
        open_ = set(rest.tolist())
        while open_:
            toegewezen = {}
            for i in open_:
                kand = {regio[j] for j in buren[i] if regio[j] >= 0 and grens[j] == grens[i]}
                if kand:
                    toegewezen[i] = max(kand, key=lambda k: F[i, regio == k].sum())
            if not toegewezen:
                for i in sorted(open_):
                    kand = {regio[j] for j in range(n) if regio[j] >= 0 and grens[j] == grens[i]}
                    if kand:
                        toegewezen[i] = max(kand, key=lambda k: F[i, regio == k].sum())
                    else:
                        regio[i] = len(namen); soort.append('rest'); namen.append(f"Rest {grens_naam[grens[i]]}")
                        toegewezen[i] = regio[i]
                        break
            for i, k in toegewezen.items():
                regio[i] = k
            open_ -= set(toegewezen)
    else:
        for c in sorted(set(corop[rest])):
            for comp in componenten(rest[corop[rest] == c]):
                regio[comp] = len(namen); soort.append('rest')
                namen.append(f"Rest {corop_naam_van[c]}" + ("" if len(componenten(rest[corop[rest] == c])) == 1 else f" {naam[max(comp, key=lambda i: won_gm[i])]}"))
        veranderd = True
        while veranderd:
            veranderd = False
            for r in [k for k in range(len(namen)) if soort[k] == 'rest']:
                leden = np.where(regio == r)[0]
                if len(leden) == 0 or won_gm[leden].sum() >= MIN_REST_WONINGEN:
                    continue
                g = grens[leden[0]]
                kand = {regio[j] for i in leden for j in buren[i] if regio[j] != r and grens[j] == g} or \
                       {regio[j] for j in range(n) if regio[j] != r and grens[j] == g}
                if kand:
                    regio[leden] = max(kand, key=lambda k: F[np.ix_(leden, np.where(regio == k)[0])].sum()); veranderd = True
    over = sorted(set(regio), key=lambda r: namen[r]); nieuw = {o: i + 1 for i, o in enumerate(over)}

    # 6. stadregio's: binnen elke pendelregio elke oorspronkelijke stad, en de overige gemeenten samen als ommeland; een stad die over
    # twee pendelregio's valt, krijgt per regio een eigen stadregio, zodat elke stadregio binnen een pendelregio blijft
    grootste_van = {c: naam[max(np.where(stad_van == c)[0], key=lambda i: inw_gm[i])] for c in steden}
    regios_van_stad = {c: set(regio[stad_van == c]) for c in steden}
    stadregio = [(f"Stad {grootste_van[stad_van[i]]}" + ("" if len(regios_van_stad[stad_van[i]]) == 1 else f" ({namen[regio[i]]})"))
                 if stad_van[i] >= 0 else f"Ommeland {namen[regio[i]]}" for i in range(n)]
    sr_namen = sorted(set(stadregio)); sr_code = {s: k + 1 for k, s in enumerate(sr_namen)}

    # uitvoer en samenvatting
    UIT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({'GM_code': codes, 'Gemeente': naam, 'Pendelregio_code': [nieuw[r] for r in regio], 'Pendelregio': [namen[r] for r in regio],
                  'Soort': [soort[r] for r in regio], 'Stadregio_code': [sr_code[s] for s in stadregio], 'Stadregio': stadregio,
                  'COROP': corop, 'Provincie': prov,
                  'Inwoners': inw_gm.round(0).astype(int), 'Woningen': won_gm.round(0).astype(int)}).to_csv(UIT, index=False, sep=',', encoding='utf-8', lineterminator='\r\n')
    def binnen_deel(r):
        return F[r[:, None] == r[None, :]].sum() / F.sum()
    _, r_corop = np.unique(corop, return_inverse=True)
    wpr = np.bincount([nieuw[r] - 1 for r in regio], weights=won_gm)
    print(f"stedelijke centra {nc}, steden na samenvoegen {len(fua_ids)}, gemeenten in een FUA {int((fua >= 0).sum())} van {n}")
    print(f"pendelregio's {len(over)} (grens {a.grens}): {binnen_deel(regio):.3f} van de pendel binnen de regio; COROP {binnen_deel(r_corop):.3f}")
    print(f"woningen per regio: kleinste {wpr.min():,.0f}, mediaan {np.median(wpr):,.0f}, grootste {wpr.max():,.0f}")
    wsr = np.bincount([sr_code[s] - 1 for s in stadregio], weights=won_gm)
    print(f"stadregio's {len(sr_namen)} (samenvoegen {a.samenvoegen}, rest {a.rest}): woningen kleinste {wsr.min():,.0f}, mediaan {np.median(wsr):,.0f}, grootste {wsr.max():,.0f}")
    print(f"geschreven: {UIT}")


if __name__ == "__main__":
    main()
