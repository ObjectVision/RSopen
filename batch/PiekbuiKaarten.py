"""Maakt uit de waterdieptekaart van 0,5 m van de Klimaateffectatlas de vier kaarten op het raster van 25 m die RSopen leest.

De levering staat per bui in vier zips (noord, oost, west en zuid) met tegels van 5 km, samen meer dan 100 GB. RSopen rekent op 25 m en de
drie indicatoren hebben elk iets anders aan de kaart van 0,5 m nodig, dus het script schrijft per bui:
- <bui>_Waterschijf_25m.tif: het watervolume in de cel gedeeld door het oppervlak van de cel, in meter, voor de opgave en de balans per blok;
- <bui>_FractieNat_25m.tif: het aandeel van de cel dat nat is. Waterschijf gedeeld door deze fractie is de diepte op het natte deel, voor de schade;
- <bui>_DiepteOpWeg_NWB<datum>_25m.tif: de gemiddelde diepte op de punten van de wegas in de cel, met droog als nul, voor de weguitval;
- <bui>_FractieNatOpWeg_NWB<datum>_25m.tif: het aandeel van die punten dat nat is, voor de weguitval.
De levering geeft droog en open water als nodata; hier zijn die nul, zoals in de oude kaarten. Een pixel zonder getal (NaN) telt als droog. De
wegkaarten horen bij een NWB-levering, dus die datum staat in de naam en een nieuwe levering vraagt een nieuwe run. Punten op de as liggen elke
5 m op dezelfde autowegen als BaseData/Wegennet.dms; de baansoorten zonder auto komen uit ModelParameters/Piekbuiberging.dms.

De kaarten zijn float32 met deflate, omdat GeoDMS op dit moment geen zstd leest (ObjectVision/GeoDMS#1332). Het script schrijft eerst <naam>.deel
en geeft pas de echte naam als de kaart af is; een bestaande kaart wordt nooit overschreven. Bij elke kaart hoort een tfw en een <naam>_meta.txt
met wat erin staat, waar de bron vandaan komt en hoe de kaart is gemaakt; per bui komt er een overzicht per tegel bij. Elke tegel wordt getoetst op de CRC in de zip. Is er een beschadigd, dan leest het script de rest nog
wel, noemt het alle beschadigde tegels en stopt het zonder iets te schrijven, want een gat in de kaart zou er als droog gebied uitzien.

Nodig: Python 3 met numpy, rasterio, pyogrio en shapely.
Gebruik: python batch/PiekbuiKaarten.py <map met zips> <bui> <versie> <Wegvakken.gpkg> <uitmap> [werkers]
Staat een zip apart, bijvoorbeeld na een nieuwe download, geef dan meer mappen op met een puntkomma ertussen; de eerste map gaat voor.
Voorbeeld: python batch/PiekbuiKaarten.py E:/SourceData 155mm_2h v20260810 E:/SourceData/RSOpen/Grondgebruik/NWB/20251101/Wegvakken/Wegvakken.gpkg C:/LocalData/Piekbui 8
"""
import csv, datetime, glob, hashlib, os, platform, re, sys, time, zipfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import numpy as np
import pyogrio, rasterio, shapely
from rasterio.errors import RasterioIOError
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

# het raster van AdminDomain
X0, Y0, CEL, BREEDTE, HOOGTE = 0.0, 625000.0, 25.0, 11200, 13000
TEGEL = 5000.0
PUNTAFSTAND = 5.0
PARAMETERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cfg', 'main', 'ModelParameters', 'Piekbuiberging.dms')
ZIPNAAM = 'wateroverlast_waterdiepte_hevige_neerslag_waterdiepte_{bui}_waterdiepte-*.zip'
DOWNLOADPAGINA = 'https://www.klimaateffectatlas.nl/nl/download-data-waterdiepte-bij-hevige-neerslag'
KAARTEN = dict(
    schijf=('{bui}_Waterschijf_25m.tif', 'Het watervolume in de cel gedeeld door het oppervlak van de cel, in meter. Voor de opgave en de balans per blok.'),
    fractie=('{bui}_FractieNat_25m.tif', 'Het aandeel van de cel dat nat is, van 0 tot 1. De waterschijf gedeeld door deze fractie is de diepte op het natte deel. Voor de schade.'),
    wegdiepte=('{bui}_DiepteOpWeg_NWB{nwb}_25m.tif', 'De gemiddelde diepte op de punten van de wegas in de cel, in meter, met droog als nul; punten elke {afstand:.0f} m. Cellen zonder autoweg zijn nul. Voor de weguitval.'),
    wegfractie=('{bui}_FractieNatOpWeg_NWB{nwb}_25m.tif', 'Het aandeel van de punten van de wegas in de cel dat nat is, van 0 tot 1; punten elke {afstand:.0f} m. Cellen zonder autoweg zijn nul. Voor de weguitval.'),
)


def kop_lezen(lid):
    zip_pad, naam = lid
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        with rasterio.open(f'zip://{zip_pad}!{naam}') as r:
            b = r.bounds
    regio = os.path.basename(zip_pad).rsplit('-', 1)[1].removesuffix('.zip')
    return dict(zip=zip_pad, lid=naam, naam=os.path.basename(naam), regio=regio, xmin=b.left, ymin=b.bottom, xmax=b.right, ymax=b.top)


def zips_zoeken(mappen, bui):
    per_regio = {}
    for m in mappen.split(';'):
        for z in sorted(glob.glob(os.path.join(m, ZIPNAAM.format(bui=bui)))):
            per_regio.setdefault(os.path.basename(z), z)
    if len(per_regio) != 4:
        sys.exit(f'verwacht vier zips voor {bui} in {mappen}, gevonden: {sorted(per_regio)}')
    return [per_regio[n] for n in sorted(per_regio)]


def tegels_lezen(zips, werkers):
    leden = []
    for z in zips:
        with zipfile.ZipFile(z) as f:
            leden += [(z, i.filename) for i in f.infolist() if i.filename.endswith('.tif')]
    with ThreadPoolExecutor(werkers) as ex:
        tegels = list(ex.map(kop_lezen, leden))
    plekken = {(t['xmin'], t['ymin']) for t in tegels}
    if len(plekken) != len(tegels):
        sys.exit(f'{len(tegels) - len(plekken)} tegels liggen op dezelfde plek en zouden dubbel tellen')
    return tegels


def wegpunten(nwb):
    with open(PARAMETERS, encoding='utf-8') as f:
        m = re.search(r"BaansoortZonderAuto.*?attribute<String> code : \[(.*?)\]", f.read(), re.S)
    zonder_auto = re.findall(r"'(\w+)'", m.group(1))
    gdf = pyogrio.read_dataframe(nwb, columns=['BST_CODE'])
    geoms = gdf.geometry.values[~gdf['BST_CODE'].isin(zonder_auto).to_numpy()]
    lengte = shapely.length(geoms)
    aantal = np.maximum(np.ceil(lengte / PUNTAFSTAND).astype(np.int64), 1)
    wegvak = np.repeat(np.arange(len(geoms)), aantal)
    start = np.r_[0, np.cumsum(aantal)[:-1]]
    afstand = (np.arange(aantal.sum()) - start[wegvak] + 0.5) * (lengte / aantal)[wegvak]
    x, y = np.empty(len(wegvak)), np.empty(len(wegvak))
    stap = 2_000_000
    for i in range(0, len(wegvak), stap):
        p = shapely.line_interpolate_point(geoms[wegvak[i:i + stap]], afstand[i:i + stap])
        x[i:i + stap], y[i:i + stap] = shapely.get_x(p), shapely.get_y(p)
    return x, y, float(lengte.sum()) / 1000


def punten_verdelen(x, y, tegels):
    """Per tegel de nummers van de wegpunten die erin vallen. Een blok van 5 km kan meer tegels hebben als de levering hem heeft afgekapt."""
    per_blok = {}
    for n, t in enumerate(tegels):
        per_blok.setdefault((int((t['xmin'] + t['xmax']) / 2 // TEGEL), int((t['ymin'] + t['ymax']) / 2 // TEGEL)), []).append(n)
    blok = (np.floor(x / TEGEL).astype(np.int64) << 20) + np.floor(y / TEGEL).astype(np.int64)
    volgorde = np.argsort(blok, kind='stable')
    grenzen = np.r_[0, np.flatnonzero(np.diff(blok[volgorde])) + 1, len(blok)]
    uit = [np.empty(0, dtype=np.int64) for _ in tegels]
    for a, b in zip(grenzen[:-1], grenzen[1:]):
        s = int(blok[volgorde[a]])
        i = volgorde[a:b]
        for n in per_blok.get((s >> 20, s & ((1 << 20) - 1)), []):
            t = tegels[n]
            ok = (x[i] >= t['xmin']) & (x[i] < t['xmax']) & (y[i] >= t['ymin']) & (y[i] < t['ymax'])
            uit[n] = i[ok]
    return uit


def lees_tegel(tegel):
    """Leest een tegel via de CRC van de zip, want die ziet ook een beschadiging waar het uitpakken van de tegel niet op valt."""
    with zipfile.ZipFile(tegel['zip']) as z:
        data = z.read(tegel['lid'])
    with rasterio.Env(GDAL_CACHEMAX=256), MemoryFile(data) as m, m.open() as r:
        return r.read(1), r.transform, r.nodata


def verwerk(taak):
    tegel, x, y, cel = taak
    try:
        a, tr, nodata = lees_tegel(tegel)
    except (zipfile.BadZipFile, RasterioIOError) as e:
        return dict(fout=f"{os.path.basename(tegel['zip'])}: {tegel['naam']}: {e}")
    nat = np.isfinite(a) & (a > 0)
    diepte = np.where(nat, a.astype(np.float64), 0.0)
    pixel_opp = abs(tr.a * tr.e)
    kol = np.floor((tr.c + (np.arange(a.shape[1]) + 0.5) * tr.a - X0) / CEL).astype(np.int64)
    rij = np.floor((Y0 - (tr.f + (np.arange(a.shape[0]) + 0.5) * tr.e)) / CEL).astype(np.int64)
    ks, rs = np.r_[0, np.flatnonzero(np.diff(kol)) + 1], np.r_[0, np.flatnonzero(np.diff(rij)) + 1]

    def som(m):
        return np.add.reduceat(np.add.reduceat(m, rs, axis=0), ks, axis=1)

    k, r_ = np.floor((x - tr.c) / tr.a).astype(np.int64), np.floor((y - tr.f) / tr.e).astype(np.int64)
    binnen = (r_ >= 0) & (r_ < a.shape[0]) & (k >= 0) & (k < a.shape[1])
    d_punt = diepte[r_[binnen], k[binnen]]
    natpunt = d_punt > 0
    return dict(
        rij=int(rij[0]), kol=int(kol[0]), volume=(som(diepte) * pixel_opp).astype(np.float32), natopp=(som(nat.astype(np.float64)) * pixel_opp).astype(np.float32),
        cel=cel[binnen][natpunt], d_punt=d_punt[natpunt].astype(np.float32),
        rij_csv=(tegel['naam'], tegel['regio'], int(a.size), int((a != nodata).sum()), int(np.isnan(a).sum()), float(diepte.sum()) * pixel_opp, float(diepte.max())),
    )


def kaart_schrijven(pad, data):
    tr = from_origin(X0, Y0, CEL, CEL)
    with rasterio.open(pad + '.deel', 'w', driver='GTiff', width=BREEDTE, height=HOOGTE, count=1, dtype='float32', crs='EPSG:28992', transform=tr,
                       tiled=True, blockxsize=256, blockysize=256, compress='deflate', predictor=2) as o:
        o.write(data.astype(np.float32), 1)
    os.replace(pad + '.deel', pad)
    with open(os.path.splitext(pad)[0] + '.tfw', 'w', encoding='ascii') as f:
        f.write(f'{tr.a}\n{tr.b}\n{tr.d}\n{tr.e}\n{tr.c + tr.a / 2}\n{tr.f + tr.e / 2}\n')


def meta_schrijven(pad, inhoud, gedeeld):
    with open(os.path.splitext(pad)[0] + '_meta.txt', 'w', encoding='utf-8') as f:
        f.write(f'Bestand: {os.path.basename(pad)}\nInhoud: {inhoud}\n{gedeeld}')


def main():
    if len(sys.argv) < 6:
        sys.exit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    map_zips, bui, versie, nwb, uitmap = sys.argv[1:6]
    werkers = int(sys.argv[6]) if len(sys.argv) > 6 else 8
    m = re.search(r'NWB[\\/](\d{8})[\\/]', nwb)
    if not m:
        sys.exit(f'geen leveringsdatum van het NWB gevonden in {nwb}')
    nwb_datum = m.group(1)
    uit = {n: os.path.join(uitmap, k[0].format(bui=bui, nwb=nwb_datum)) for n, k in KAARTEN.items()}
    for p in uit.values():
        if os.path.exists(p):
            sys.exit(f'{p} bestaat al en wordt niet overschreven')
    os.makedirs(uitmap, exist_ok=True)

    t0 = time.time()
    zips = zips_zoeken(map_zips, bui)
    tegels = tegels_lezen(zips, werkers)
    print(f'{len(tegels)} tegels, {time.time() - t0:.0f} s', flush=True)
    x, y, netlengte = wegpunten(nwb)
    print(f'{len(x):,} punten op {netlengte:,.0f} km autoweg, {time.time() - t0:.0f} s', flush=True)
    cel = np.floor((Y0 - y) / CEL).astype(np.int64) * BREEDTE + np.floor((x - X0) / CEL).astype(np.int64)
    if cel.min() < 0 or cel.max() >= HOOGTE * BREEDTE:
        sys.exit('er liggen wegpunten buiten het raster')
    weg_n = np.bincount(cel, minlength=HOOGTE * BREEDTE).astype(np.float32)
    per_tegel = punten_verdelen(x, y, tegels)
    gevonden = sum(len(i) for i in per_tegel)
    print(f'{len(x) - gevonden:,} punten vallen buiten elke tegel en tellen als droog, {time.time() - t0:.0f} s', flush=True)

    volume = np.zeros((HOOGTE, BREEDTE), dtype=np.float32)
    natopp = np.zeros((HOOGTE, BREEDTE), dtype=np.float32)
    weg_som = np.zeros(HOOGTE * BREEDTE, dtype=np.float32)
    weg_nat = np.zeros(HOOGTE * BREEDTE, dtype=np.float32)
    regels, fouten = [], []
    werk = ((t, x[i], y[i], cel[i]) for t, i in zip(tegels, per_tegel))
    with ProcessPoolExecutor(werkers) as ex:
        for n, u in enumerate(ex.map(verwerk, werk, chunksize=1)):
            if 'fout' in u:
                fouten.append(u['fout'])
                print(u['fout'], flush=True)
                continue
            r0, k0 = u['rij'], u['kol']
            r1, k1 = min(r0 + u['volume'].shape[0], HOOGTE), min(k0 + u['volume'].shape[1], BREEDTE)
            ra, ka = max(r0, 0), max(k0, 0)
            deel = (slice(ra - r0, r1 - r0), slice(ka - k0, k1 - k0))
            volume[ra:r1, ka:k1] += u['volume'][deel]
            natopp[ra:r1, ka:k1] += u['natopp'][deel]
            np.add.at(weg_som, u['cel'], u['d_punt'])
            np.add.at(weg_nat, u['cel'], 1)
            regels.append(u['rij_csv'])
            if n % 100 == 0:
                print(f'{n}/{len(tegels)} tegels, {time.time() - t0:.0f} s', flush=True)
    if fouten:
        sys.exit(f'{len(fouten)} tegels zijn beschadigd en er is niets geschreven; download de zips hieronder opnieuw:\n' + '\n'.join(fouten))

    opp = CEL * CEL
    heeft_weg = weg_n > 0
    wegdiepte = np.zeros_like(weg_som)
    wegfractie = np.zeros_like(weg_som)
    wegdiepte[heeft_weg] = weg_som[heeft_weg] / weg_n[heeft_weg]
    wegfractie[heeft_weg] = weg_nat[heeft_weg] / weg_n[heeft_weg]
    kaart_schrijven(uit['schijf'], volume / opp)
    kaart_schrijven(uit['fractie'], natopp / opp)
    kaart_schrijven(uit['wegdiepte'], wegdiepte.reshape(HOOGTE, BREEDTE))
    kaart_schrijven(uit['wegfractie'], wegfractie.reshape(HOOGTE, BREEDTE))

    with open(os.path.join(uitmap, f'{bui}_tegels.csv'), 'w', newline='', encoding='utf-8') as f:
        c = csv.writer(f, delimiter=';')
        c.writerow(['naam', 'regio', 'pixels', 'geldig', 'nan', 'volume_m3', 'maxdiepte_m'])
        c.writerows(regels)
    vol_tegels = sum(r[5] for r in regels)
    vol_kaart = float(volume.astype(np.float64).sum())
    with open(os.path.abspath(__file__), 'rb') as f:
        script_hash = hashlib.sha256(f.read()).hexdigest()
    nan_pixels = sum(r[4] for r in regels)
    zip_regels = ''.join(
        f"  {os.path.basename(z)}: {os.path.getsize(z) / 1e9:.2f} GB, bestandsdatum {datetime.datetime.fromtimestamp(os.path.getmtime(z)):%Y-%m-%d %H:%M}, {sum(t['zip'] == z for t in tegels)} tegels\n"
        for z in zips)
    versies = f'Python {platform.python_version()}, numpy {np.__version__}, rasterio {rasterio.__version__}, GDAL {rasterio.__gdal_version__}, shapely {shapely.__version__}, pyogrio {pyogrio.__version__}'
    gedeeld = f"""Raster: RD (EPSG:28992), oorsprong {X0:.0f}, {Y0:.0f}, cellen van {CEL:.0f} m, {BREEDTE} bij {HOOGTE} cellen, float32 met deflate, zonder nodata. Droog en open water zijn nul.

Bron
Dataset: Klimaateffectatlas, Waterdiepte bij korte extreme regen, bui {bui}, versie {versie}: de maximale waterdiepte op 0,5 m, doorgerekend door Nelen & Schuurmans.
Gedownload van: {DOWNLOADPAGINA}
Licentie: CC BY 4.0, bronvermelding "Klimaateffectatlas, 2026".
Zips:
{zip_regels}Wegen: NWB-levering {nwb_datum}, {os.path.basename(nwb)}, zonder de baansoorten in ModelParameters/Piekbuiberging/Weguitval/BaansoortZonderAuto ({len(x):,} punten op {netlengte:,.0f} km). Alleen de wegkaarten lezen dit.

Bewerking
Gemaakt op {datetime.datetime.now():%Y-%m-%d %H:%M} met batch/PiekbuiKaarten.py uit de repo van RSopen, sha256 {script_hash}.
Aanroep: python batch/PiekbuiKaarten.py <map met zips> {bui} {versie} <Wegvakken.gpkg> <uitmap> {werkers}
Versies: {versies}.
De tegels zijn rechtstreeks uit de zips gelezen, zonder uit te pakken. Per cel van {CEL:.0f} m is opgeteld hoeveel water er in de pixels van 0,5 m staat en hoeveel pixels nat zijn. De levering geeft droog en open water als nodata; die tellen hier als droog, net als een pixel zonder getal (NaN). Onder een pand staat geen water in de levering. De wegkaarten lezen de pixel op de as op punten elke {PUNTAFSTAND:.0f} m en middelen die per cel.

Controle
De CRC in de zip klopt voor alle {len(tegels)} tegels. Het volume is {vol_tegels / 1e6:,.1f} mln m3, in de tegels en in de kaart gelijk tot op {abs(vol_tegels - vol_kaart) / 1e6:.3f} mln m3. {nan_pixels} pixels zonder getal. {len(x) - gevonden:,} van de {len(x):,} wegpunten vallen buiten elke tegel en tellen als droog.
"""
    for n, (_, inhoud) in KAARTEN.items():
        meta_schrijven(uit[n], inhoud.format(afstand=PUNTAFSTAND), gedeeld)
    print(f'volume mln m3: tegels {vol_tegels / 1e6:.3f}, kaart {vol_kaart / 1e6:.3f}')
    print(f'KLAAR {time.time() - t0:.0f} s')


if __name__ == '__main__':
    main()
