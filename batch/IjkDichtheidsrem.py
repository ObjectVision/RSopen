r"""IJkt de factoren voor de kerngrootte in de dichtheidsrem aan de echte nieuwbouw van een periode (#879, #899).

Gebruik (op een regel):
    python batch\IjkDichtheidsrem.py --werkkopie <werkkopie> --periode 2012-2021
        [--voorraad <tif>] (--nieuwbouw <npz> | --bag-store <map>) --rem-export <map> [--kernbuffers <map>]
        --bbg <tif> --cbs <gpkg> --nvm <tif> --contour <npy, tif of gpkg> --uitvoer <map>
        [--variant BAU] [--aandeel 0.9]

Voorbeeld, met de voorraad en de nieuwbouw uit een levering van de BAG:
    python batch\IjkDichtheidsrem.py --werkkopie . --periode 2012-2021
        --bag-store %SourceDataDir%\RSopen\Vastgoed\BAG_20261008_History
        --rem-export %LocalDataProjDir%\Ijking\remfactor --kernbuffers %LocalDataProjDir%\BaseData\PopBuffers
        --bbg %LocalDataProjDir%\BaseData\Grondgebruik\BBG\BBG2022_100m_Modus_Nederland.tif
        --cbs %SourceDataDir%\RSopen\RegioIndelingen\cbsgebiedsindelingen2024.gpkg --nvm %LocalDataProjDir%\Ijking\nvm.tif
        --contour %LocalDataProjDir%\Ijking\BG2012_NL.gpkg --uitvoer %LocalDataProjDir%\Ijking
%SourceDataDir% en %LocalDataProjDir% staan voor de mappen die GeoDMS onder die namen kent; vul ze zelf in.

Wat de rem is. De zeef laat een ontwikkelpakket niet toe in een blok van 100 m waar zijn dichtheid boven de rem van zijn
subsector ligt (Templates/Beschikbaarheden/Zeef_Wonen_perOP_T, Dichtheid). De rem (Templates/Densities/MaxWoningDichtheid_T,
Result) is het grootste van twee waarden. De eerste is de ondergrens: de dichtheid van het dunste pakket van de subsector.
Binnen de buffer rond de kernen is dat het dunste pakket met rijtjeswoningen, als dat dichter is. Die waarde wordt gemiddeld
over de zestien cellen van het blok. De tweede waarde is het omgevingsmaximum maal de dichtheidsfactor, uitgesmeerd over de
blokken binnen 2 km met een gewicht dat met de afstand afneemt. Het omgevingsmaximum is per blok het hoogste van de eigen
woningdichtheid en de gemiddelde dichtheid van de woonblokken in de buurt, wijk, gemeente, NVM-regio, COROP en provincie. De
dichtheidsfactor is de generieke factor plus de opslagen voor OV, groot water en de grootte van de kern bij het blok. Ligt een
blok in de buffers van meer kernklassen, dan telt alleen de opslag van de grootste klasse. De factoren staan per woningtype in
VariantK.dms.

Wat het script doet. Het rekent de rem na zoals MaxWoningDichtheid_T hem rekent, zodat het per blok kan terugrekenen bij welke
factor de rem een gegeven dichtheid toelaat. Het legt de echte nieuwbouw van de periode tegen de rem zoals het model die in het
beginjaar gehad zou hebben: het omgevingsmaximum uit de voorraad van het beginjaar, de factoren en de pakketten uit de
werkkopie. Per blok neemt het de nieuwe woningen van een type, op de blokken waar dat type de meerderheid heeft; een blok is een
hectare, dus het aantal is de dichtheid. Per blok volgt daaruit de factor voor de kernklasse waarbij de rem precies die
dichtheid toelaat, met de andere factoren op hun stand. De ijkwaarde is de factor waaronder het opgegeven aandeel van de nieuwe
woningen blijft, per type, kernklasse en ligging (binnen of buiten het bebouwd gebied van het beginjaar), voor Nederland en voor
Noord- en Zuid-Holland (de constante DEELGEBIED). Dat gebeurt zonder en met de ondergrens: een blok op of onder de ondergrens
komt bij elke factor door. De BAG kent geen vrije sector of sociale huur, en die twee hebben elk een eigen ondergrens. De tabel
geeft daarom per type de ijking met de ondergrens van de vrije sector en met die van de sociale huur.

Welke waarde uit de tabel de factor in VariantK.dms wordt, is een afweging per kernklasse, bijvoorbeeld tussen binnen en buiten
of tussen het landelijke getal en dat van Noord- en Zuid-Holland. Die afweging staat in #879 en in de Descr van de factoren in
VariantK.dms; het script maakt hem niet.

De invoer:
  --werkkopie    een werkkopie van RSopen. Het script leest VariantK.dms (de factoren, kolom --variant), Default_src.dms
                 (de pakketten, met de kolomindeling uit OPTabel_T.dms en nrAttr uit NettoBuurt.dms), ModelParameters/Wonen.dms
                 (vormfactoren, bouwlaaghoogte en hoogbouwgrens), MaxWoningDichtheid_T.dms (de straal van de kegel) en, met
                 --bag-store, BAG_RecentYear uit ModelParameters.dms.
  --voorraad     de woningen per cel van 25 m op 1 januari van het beginjaar. Zonder dit argument telt het script ze uit
                 --bag-store: de woon-vbo's in de jaarset van die datum.
  --nieuwbouw    een npz met per cel van 25 m de nieuwe woningen, eengezins en meergezins, zoals het script hem met
                 --bag-store zelf in de uitvoermap zet.
  --bag-store    de store van BAG-Tools (pand.mmd en vbo.mmd). Het script leest hem zoals SourceData/Vastgoed/BAG.dms: de
                 nieuwbouw zijn de woon-vbo's in de jaarset van 1 januari na het eindjaar met een bouwjaar vanaf het beginjaar,
                 en het type volgt uit het aantal woon-vbo's in het pand (een is eengezins, meer is meergezins).
  --rem-export   een map met rem_OV_100m.tif en rem_Water_100m.tif: per blok van 100 m het gemiddelde over de zestien cellen
                 van BaseData/Omgeving/OV_Reistijd/TotRailHalte/Smoothed en BaseData/StartState/Landgebruik/
                 NabijGrootWaterInBBG/Smoothed. Het model schrijft die twee alleen op aanvraag weg, met de container
                 Diagnose/Wonen/IjkingDichtheidsrem naar %LocalDataProjDir%/Ijking/remfactor. Zonder
                 --kernbuffers leest het script ook de kernklassen hier, als rem_K100_100m.tif, rem_K20_100m.tif en
                 rem_K20min_100m.tif, elk al zo dat een blok alleen bij zijn grootste kernklasse telt.
  --kernbuffers  %LocalDataProjDir%/BaseData/PopBuffers van een run: de buffers van een kilometer rond de kernen per klasse
                 (UrbanContour_<klasse>_<studiegebied>_25m.tif), die WriteBasedata wegschrijft en het model als
                 BaseData/Omgeving/BebouwdGebied/RondBevolkingskern leest.
  --bbg          de dominante BBG-klasse per blok van 100 m, BaseData/Grondgebruik/BBG/BBG<jaar>_100m_Modus_<studiegebied>.tif;
                 een blok is woonlocatie als die klasse Woonterrein is. De ijking voor #879 gebruikte de BBG van 2022, het
                 basisjaar van het model, ook bij een periode vanaf 2012; een BBG van het beginjaar is niet uitgeprobeerd.
  --cbs          een CBS-gebiedsindeling (gpkg) met de lagen van CBS_LAGEN; de provincies geven ook het deelgebied.
  --nvm          de NVM-regio per cel van 25 m (tif), een geheel getal per regio; het script gebruikt alleen de indeling,
                 niet de nummers. Diagnose/Wonen/IjkingDichtheidsrem/NVM schrijft hem op aanvraag weg.
  --contour      het bebouwd gebied van het beginjaar: een npy of tif van 25 m op het referentiegrid, of vlakken (gpkg, shp).
                 De ijking voor #879 gebruikte het bebouwd gebied van 2012 als npy op het referentiegrid.
  De nieuwbouw kan alleen als npz (--nieuwbouw) of uit de store (--bag-store) binnenkomen, niet als tif.

Schrijft <uitvoer>/IjkDichtheidsrem_<begin>_<eind>.txt en, met --bag-store, bag_nieuw_<begin>_<eind>_per_type.npz in
dezelfde map. Leest verder alleen.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyogrio
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from scipy.signal import fftconvolve

# Het referentiegrid van het model voor Nederland: cellen van 25 m vanaf (0, 625000) in RD, en blokken van 4 bij 4 cellen
# (100 m, een hectare), het AllocDomain waarop de rem werkt.
H, W = 13000, 11200
X0, Y0 = 0.0, 625000.0
CEL = 25.0
BLOK = 4
H1, W1 = H // BLOK, W // BLOK
M2_PER_HA = 1e4
CEL_HA = CEL * CEL / M2_PER_HA
TR = from_origin(X0, Y0, CEL, CEL)
TR1 = from_origin(X0, Y0, CEL * BLOK, CEL * BLOK)

# De woningtypen met hun korte naam in VariantK.dms en Default_src.dms, en de subsectoren van Classifications/Vastgoed/WP2xVSSH.
TYPEN = [('eengezins', 'EG'), ('meergezins', 'MG')]
SUBS = ['eengezins_VrijeSector', 'eengezins_SocialeHuur', 'meergezins_VrijeSector', 'meergezins_SocialeHuur']

# De kernklassen in de volgorde van de switch in MaxWoningDichtheid_T (DichtheidFactor_AdminDomain): een cel in de buffer van
# meer klassen telt bij de eerste. Per klasse de korte naam, de tekst in de tabel, het achtervoegsel van de factor in
# VariantK.dms en de naam van de klasse in de bufferkaarten van BaseData/PopBuffers.
KLASSEN = [('K100', 'vanaf 100.000', 'BevKern100kPlus', 'isMeerdan100Kinw'),
           ('K20', '20.000 tot 100.000', 'BevKern20kPlus', 'isMeerdan20Kinw'),
           ('K20min', 'onder 20.000', 'BevKern20kMin', 'isMinderdan20Kinw')]
# De factoren van de rem: korte naam en naam in VariantK.dms (DichtheidFactor<naam>_EG en _MG).
FACTOREN = {'gen': 'Generiek', 'ov': 'OV', 'water': 'Water', **{k: n for k, _, n, _ in KLASSEN}}

# Het deelgebied naast Nederland: label in de tabel, naam in de tekst, en de provincies met hun statnaam in de CBS-gebiedsindeling.
DEELGEBIED = ('NH+ZH', 'Noord- en Zuid-Holland', ('Noord-Holland', 'Zuid-Holland'))

# De regio's waarover MaxWoningDichtheid_T het gemiddelde neemt, als lagen van --cbs; de NVM-regio komt uit --nvm.
CBS_LAGEN = ['buurt_gegeneraliseerd', 'wijk_gegeneraliseerd', 'gemeente_gegeneraliseerd', 'coropgebied_gegeneraliseerd',
             'provincie_gegeneraliseerd']
PROVINCIE_LAAG = 'provincie_gegeneraliseerd'
NVM_CEL_IN_BLOK = 2                # de NVM-regio van een blok is die van zijn cel op rij en kolom 2, een van de vier middelste
GEODMS_NULL_UINT32 = 2 ** 32 - 1   # zo staat een cel zonder regio in een tif van UInt32 die GeoDMS schreef

# Een blok is woonlocatie als zijn dominante BBG-klasse Woonterrein is, id 5 in Classifications/Grondgebruik/CBSKlasse2020.
WOONTERREIN = 5

# Drempels van de meting.
DEKKING_KERNKLASSE = 0.5   # een blok hoort bij de eerste kernklasse waarvan de buffer minstens dit deel van het blok dekt
BINNEN_MIN_CELLEN = 8      # een blok ligt binnen het bebouwd gebied als minstens zoveel van zijn 16 cellen erin liggen
MIN_NIEUW_BLOK = 1         # een blok telt voor een type vanaf zoveel nieuwe woningen van dat type
MIN_KERNGEWICHT = 1e-6     # een blok telt voor een kernklasse als de gladgestreken Max maal die buffer groter is (woningen per ha);
                           # daaronder verzet de factor van de klasse de rem van het blok niet

# De bestanden in --rem-export en --kernbuffers.
EXPORT = 'rem_{naam}_100m.tif'
KERNBUFFER = 'UrbanContour_{klasse}_*.tif'

# De bestanden in de werkkopie.
VARIANTK = 'cfg/main/VariantParameters/VariantK.dms'
PAKKETTEN = 'cfg/main/VariantParameters/Ontwikkelpakketten/NettoBuurt/Default_src.dms'
PAKKETKOLOMMEN = 'cfg/main/VariantParameters/Ontwikkelpakketten/NettoBuurt/OPTabel_T.dms'
NETTOBUURT = 'cfg/main/VariantParameters/Ontwikkelpakketten/NettoBuurt.dms'
WONEN = 'cfg/main/ModelParameters/Wonen.dms'
MODELPARAMETERS = 'cfg/main/ModelParameters.dms'
REM = 'cfg/main/Templates/Densities/MaxWoningDichtheid_T.dms'

# De BAG-store, gelezen zoals SourceData/Vastgoed/BAG.dms (PerJaar_T): de statussen van de voorraad volgens
# Classifications/Vastgoed/BAG.dms, de datumregels van de lezer en de grenzen van het bouwjaar.
VOORRAAD_PAND = {'pand buiten gebruik', 'pand in gebruik', 'pand in gebruik (niet ingemeten)', 'verbouwing pand'}
VOORRAAD_VBO = {'verblijfsobject buiten gebruik', 'verblijfsobject in gebruik', 'verblijfsobject in gebruik (niet ingemeten)',
                'verbouwing verblijfsobject'}
OPEN_DATUM = 20500101            # MaxDatum: een begin- of einddatum 0 is open
REGISTRATIE_VOOR = 19600101      # een pandvoorkomen met een datum hiervoor neemt de registratiedatum
BOUWJAAR_ONBEKEND_TOT = 1005     # een bouwjaar tot en met dit jaar is onbekend (Bouwjaar_truncation_Expr)
BOUWJAAR_MINIMUM = 1500          # een bekend bouwjaar hiervoor wordt dit jaar
KADER_NL_MM = (0, 300_000_000, 300_000_000, 620_000_000)   # x van, x tot, y van, y tot in mm RD: de vbo's in Nederland
MM = 1000


def stop(melding):
    sys.exit(f'Gestopt: {melding}')


def eerste_januari(jaar):
    """De peildatum 1 januari van een jaar als jjjjmmdd, zoals de BAG-store hem schrijft."""
    return jaar * 10000 + 101


def meld(tekst):
    print(tekst, flush=True)


# ---------- de werkkopie ----------

def lees_cfg(werkkopie, rel):
    pad = werkkopie / rel
    if not pad.is_file():
        stop(f'{pad} bestaat niet; is {werkkopie} een werkkopie van RSopen?')
    return pad.read_text(encoding='utf-8')


def getal(tekst, naam, bestand):
    """Een parameter met een vaste waarde, zoals 'parameter<meter> Hoogbouwgrens := 15[meter]'."""
    m = re.search(rf'\b{naam}\s*:=\s*([0-9]+(?:\.[0-9]+)?)', tekst)
    if not m:
        stop(f'{naam} niet gevonden in {bestand}')
    return float(m.group(1))


def factoren(werkkopie, variant):
    """De factoren van de rem per woningtype uit de kolom van de variant in VariantK.dms. Stopt als de variant eigen
    pakketten toevoegt, want dan is Default_src.dms niet de hele set."""
    tekst = lees_cfg(werkkopie, VARIANTK)
    m = re.search(r'attribute<\w+>\s+name\s*:\s*\[([^\]]*)\]', tekst)
    namen = re.findall(r"'([^']*)'", m.group(1)) if m else []
    if variant not in namen:
        stop(f'variant {variant} staat niet in {VARIANTK} (varianten: {", ".join(namen)})')
    kolom = namen.index(variant)

    def waarde(item):
        m = re.search(rf'\b{item}\s*:\s*\[([^\]]*)\]', tekst)
        if not m:
            stop(f'{item} niet gevonden in {VARIANTK}')
        w = [v.strip().strip("'") for v in m.group(1).split(',')]
        if len(w) != len(namen):
            stop(f'{item} in {VARIANTK} heeft {len(w)} waarden voor {len(namen)} varianten')
        return w[kolom]

    if waarde('OP_Aanvulling').lower() != 'geen':
        stop(f'variant {variant} zet eigen pakketten achter de default-rijen (OP_Aanvulling); dit script leest alleen Default_src.dms')
    return {typ: {k: float(waarde(f'DichtheidFactor{n}_{kort}')) for k, n in FACTOREN.items()} for typ, kort in TYPEN}


def tekstvelden(tekst):
    """De velden van 'attribute<String> Text: [...]' in Default_src.dms, zonder de commentregels."""
    m = re.search(r'attribute<String>\s+Text\s*:\s*\[', tekst)
    if not m:
        stop(f'geen Text-attribuut in {PAKKETTEN}')
    i, velden = m.end(), []
    while tekst[i] != ']':
        if tekst[i] == "'":
            j = tekst.index("'", i + 1)
            velden.append(tekst[i + 1:j])
            i = j + 1
        elif tekst.startswith('//', i):
            i = tekst.index('\n', i)
        else:
            i += 1
    return velden


def pakketten(werkkopie):
    """De reguliere ontwikkelpakketten uit Default_src.dms, met de kolomindeling van OPTabel_T.dms."""
    m = re.search(r'parameter<\w+>\s+nrAttr\s*:=\s*(\d+)', lees_cfg(werkkopie, NETTOBUURT))
    if not m:
        stop(f'nrAttr niet gevonden in {NETTOBUURT}')
    nr = int(m.group(1))
    kol = {n: int(i) for n, i in re.findall(
        r'attribute<[^>]+>\s+(\w+)\s*:=\s*Elements/Text\[value\(uint32\(id\(\.\)\)\s*\*\s*nrAttr\s*\+\s*(\d+)\s*,', lees_cfg(werkkopie, PAKKETKOLOMMEN))}
    nodig = ['name', 'WP2_name_short', 'VSSH_name_short', 'Woonoppervlakte_woning', 'FloorSpaceIndex', 'GroundSpaceIndex', 'WP4_name']
    if any(n not in kol for n in nodig):
        stop(f'kolom {[n for n in nodig if n not in kol]} niet gevonden in {PAKKETKOLOMMEN}')
    tekst = lees_cfg(werkkopie, PAKKETTEN)
    velden = tekstvelden(tekst)
    if len(velden) % nr:
        stop(f'{PAKKETTEN}: {len(velden)} velden, geen veelvoud van nrAttr {nr}')
    rijen = [velden[i:i + nr] for i in range(0, len(velden), nr)]
    m = re.search(r'Range\(uint32,\s*0,\s*nrAttr\s*\*\s*(\d+)\)', tekst)
    if m and int(m.group(1)) != len(rijen):
        stop(f'{PAKKETTEN}: {len(rijen)} rijen gelezen, de eenheid zegt {m.group(1)}')
    return [dict(naam=r[kol['name']], eg=r[kol['WP2_name_short']].strip().upper() == 'EG', vs=r[kol['VSSH_name_short']].strip().upper() == 'VS',
                 opp=float(r[kol['Woonoppervlakte_woning']]), fsi=float(r[kol['FloorSpaceIndex']]), gsi=float(r[kol['GroundSpaceIndex']]),
                 wp4=r[kol['WP4_name']].strip().lower()) for r in rijen]


def gladstraal(werkkopie):
    """De straal van de kegel waarmee MaxWoningDichtheid_T de rem gladstrijkt (ResultMaalFactor), in meter."""
    m = re.search(r'ResultMaalFactor[^\n]*Distmatrices_(\d+)m/pot(\d+)m/rev_dist_scaled', lees_cfg(werkkopie, REM))
    if not m:
        stop(f'de gladstrijking van ResultMaalFactor niet gevonden in {REM}')
    if float(m.group(1)) != CEL * BLOK:
        stop(f'{REM} strijkt glad op {m.group(1)} m, het script rekent op blokken van {CEL * BLOK:.0f} m')
    return float(m.group(2))


def commit(werkkopie):
    r = subprocess.run(['git', '-C', str(werkkopie), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True)
    if r.returncode:
        return 'geen git-werkkopie'
    gewijzigd = subprocess.run(['git', '-C', str(werkkopie), 'status', '--porcelain', '--', VARIANTK, PAKKETTEN, PAKKETKOLOMMEN,
                                NETTOBUURT, WONEN, REM], capture_output=True, text=True).stdout.strip()
    return f'commit {r.stdout.strip()}' + (', met lokale wijzigingen in de gelezen bestanden' if gewijzigd else '')


# ---------- rasters ----------

def op_grid(a, t, cel, h, w, vul):
    """Legt een kaart met transform t op het referentiegrid met cellen van cel meter (h bij w cellen)."""
    if abs(t.a - cel) > 1e-6 or abs(t.e + cel) > 1e-6 or abs(t.b) > 1e-9 or abs(t.d) > 1e-9:
        stop(f'een kaart heeft cellen van {t.a} bij {-t.e} m, verwacht {cel} m')
    c0, r0 = int(round((t.c - X0) / cel)), int(round((Y0 - t.f) / cel))
    uit = np.full((h, w), vul, dtype=a.dtype)
    rs, cs, re_, ce = max(0, r0), max(0, c0), min(h, r0 + a.shape[0]), min(w, c0 + a.shape[1])
    if re_ > rs and ce > cs:
        uit[rs:re_, cs:ce] = a[rs - r0:re_ - r0, cs - c0:ce - c0]
    return uit


def lees_kaart(pad, cel, h, w, dtype, vul=0):
    """Een kaart op het referentiegrid; nodata, NaN en wat buiten de kaart valt worden vul."""
    if not Path(pad).is_file():
        stop(f'{pad} bestaat niet')
    with rasterio.open(pad) as ds:
        a = ds.read(1)
        nd = ds.nodata
        t = ds.transform
    a = a.astype(dtype)
    if a.dtype.kind == 'f':
        a[~np.isfinite(a)] = vul
    if nd is not None and np.isfinite(nd):
        a[a == nd] = vul
    return op_grid(a, t, cel, h, w, vul)


def blok(a):
    """Telt een kaart van 25 m op tot blokken van 100 m."""
    return a.reshape(a.shape[0] // BLOK, BLOK, a.shape[1] // BLOK, BLOK).sum(axis=(1, 3))


def kernbuffers(map_):
    """De drie kernklassen per blok uit de bufferkaarten van 25 m, met de voorrang van de switch, als aandeel van het blok."""
    eerder = np.zeros((H, W), bool)
    uit = {}
    for k, _, _, klasse in KLASSEN:
        f = sorted(map_.glob(KERNBUFFER.format(klasse=klasse)))
        if len(f) != 1:
            stop(f'in {map_} {len(f)} kaarten voor {KERNBUFFER.format(klasse=klasse)}, verwacht een')
        b = lees_kaart(f[0], CEL, H, W, np.uint8) > 0
        uit[k] = (blok((b & ~eerder).astype(np.float32)) / (BLOK * BLOK)).astype(np.float64)
        eerder |= b
    return uit


def contour(pad):
    """Het bebouwd gebied van het beginjaar per cel van 25 m: een npy of tif op het referentiegrid, of vlakken (celmidden)."""
    pad = Path(pad)
    if not pad.exists():
        stop(f'{pad} bestaat niet')
    if pad.suffix.lower() == '.npy':
        a = np.load(pad)
        if a.shape != (H, W):
            stop(f'{pad} heeft vorm {a.shape}, verwacht {(H, W)}')
        return a.astype(bool)
    if pad.suffix.lower() in ('.tif', '.tiff'):
        return lees_kaart(pad, CEL, H, W, np.float32) > 0
    d = pyogrio.read_dataframe(pad)
    return features.rasterize(((g, 1) for g in d.geometry if g is not None), out_shape=(H, W), transform=TR, fill=0, dtype='uint8').astype(bool)


# ---------- de BAG-store ----------

def woon_vbos(store, peil, bouwjaar_max):
    """De woon-vbo's in de jaarset van peildatum peil (jjjjmmdd): x en y in mm, het type (1 eengezins, 2 meergezins, 0 zonder
    pand) en het bouwjaar (-1 onbekend). Een vbo hangt aan het pand met het jongste bouwjaar onder zijn panden in de jaarset, bij
    gelijk bouwjaar het eerste (#839); een pand met meer dan een woon-vbo is meergezins (AfleidingPandtype.dms). Wijkt op een punt
    af van de lezer van het model: die gooit ook panden met een omvang van meer dan een kilometer weg, en daar zijn de pandvlakken
    voor nodig."""
    def labels(obj):
        pad = store / f'{obj}.mmd' / 'status' / 'Label'
        idx = np.fromfile(pad, dtype=np.uint64).reshape(-1, 2)
        seq = open(str(pad) + '.seq', 'rb').read()
        return [seq[a:b].decode('utf-8').lower() for a, b in idx]

    def lees(obj, *naam, dtype=np.int32):
        return np.fromfile(store.joinpath(f'{obj}.mmd', *naam), dtype=dtype)

    def datums(obj, met_registratie):
        b, e = lees(obj, 'meta', 'BEGINDATUM'), lees(obj, 'meta', 'EINDDATUM')
        b, e = np.where(b == 0, OPEN_DATUM, b), np.where(e == 0, OPEN_DATUM, e)
        if met_registratie:
            b = np.where(b < REGISTRATIE_VOOR, lees(obj, 'meta', 'TIJDSTIPREGISTRATIE'), b)
            e = np.where(e < REGISTRATIE_VOOR, lees(obj, 'meta', 'EINDREGISTRATIE'), e)
        return b, e

    if not (store / 'pand.mmd').is_dir() or not (store / 'vbo.mmd').is_dir():
        stop(f'{store} is geen BAG-store: pand.mmd of vbo.mmd ontbreekt')
    # panden in de jaarset; rlookup op pandnummer neemt het eerste voorkomen
    voor = np.array([lb in VOORRAAD_PAND for lb in labels('pand')])
    b, e = datums('pand', True)
    rij = np.nonzero(voor[lees('pand', 'meta', 'status_rel', dtype=np.uint8)] & (b < peil) & (e >= peil))[0]
    pid = lees('pand', 'identificatie', dtype=np.uint64)[rij]
    bj = lees('pand', 'oorspronkelijkBouwjaar', dtype=np.int16).astype(np.int32)[rij]
    bj = np.where((bj <= BOUWJAAR_ONBEKEND_TOT) | (bj > bouwjaar_max), -1, np.maximum(bj, BOUWJAAR_MINIMUM))
    o = np.argsort(pid, kind='stable')
    eerste = np.ones(len(o), bool)
    eerste[1:] = pid[o][1:] != pid[o][:-1]
    p_sort, p_pos = pid[o][eerste], o[eerste]
    del b, e, rij, o, eerste
    # vbo's in de jaarset
    voor = np.array([lb in VOORRAAD_VBO for lb in labels('vbo')])
    st = lees('vbo', 'meta', 'status_rel', dtype=np.uint8)
    b, e = datums('vbo', False)
    g = lees('vbo', 'geometry').reshape(-1, 2)
    x, y = g[:, 0].astype(np.int64), g[:, 1].astype(np.int64)
    nul = np.iinfo(np.int32).min
    in_nl = (g[:, 0] != nul) & (g[:, 1] != nul) & (x > KADER_NL_MM[0]) & (x < KADER_NL_MM[1]) & (y > KADER_NL_MM[2]) & (y < KADER_NL_MM[3])
    n_vbo = len(st)
    woon = np.unpackbits(lees('vbo', 'gebruiksdoelen', 'woon', dtype=np.uint8), bitorder='little')[:n_vbo].astype(bool)
    v_set = voor[st] & (b < peil) & (e >= peil) & in_nl
    del b, e, st, g
    # relaties vbo-pand van de jaarset
    vr = lees('vbo', 'gerelateerdPand', 'vbo_rel', dtype=np.uint32).astype(np.int64)
    rp = lees('vbo', 'gerelateerdPand', 'pand_id', dtype=np.uint64)
    k = np.clip(np.searchsorted(p_sort, rp), 0, len(p_sort) - 1)
    rel = v_set[vr] & (p_sort[k] == rp)
    vr, ppos = vr[rel], p_pos[k[rel]]
    rbj = bj[ppos]
    # per vbo de eerste relatie met het jongste bouwjaar, anders de eerste
    jong = np.full(n_vbo, -1, np.int32)
    np.maximum.at(jong, vr, rbj)
    is_jong = (rbj == jong[vr]) & (rbj >= 0)
    sleutel = vr * 2 + (~is_jong).astype(np.int64)
    o = np.argsort(sleutel, kind='stable')
    s_sorted = sleutel[o]
    first = np.ones(len(o), bool)
    first[1:] = s_sorted[1:] != s_sorted[:-1]
    keuze = np.full(n_vbo, -1, np.int64)
    for want in (1, 0):  # de jongste (even sleutel) overschrijft de terugval
        sel = first & ((s_sorted % 2) == want)
        keuze[s_sorted[sel] // 2] = o[sel]
    heeft = keuze >= 0
    v_pand = np.where(heeft, ppos[np.maximum(keuze, 0)], -1)
    v_bj = np.where(heeft, bj[np.maximum(v_pand, 0)], -1)
    # woon-vbo's per pand, als relaties geteld, en het type van het pand
    woon_vbos_pand = np.bincount(ppos[woon[vr]], minlength=len(pid))
    typ_pand = np.where(woon_vbos_pand > 1, 2, np.where(woon_vbos_pand == 1, 1, 0))
    v_typ = np.where(heeft, typ_pand[np.maximum(v_pand, 0)], 0)
    s = v_set & woon
    return x[s], y[s], v_typ[s], v_bj[s]


def naar_grid(x, y):
    """Telt punten in mm RD per cel van 25 m op het referentiegrid."""
    r = (int(Y0 * MM) - y) // int(CEL * MM)
    k = (x - int(X0 * MM)) // int(CEL * MM)
    ok = (r >= 0) & (r < H) & (k >= 0) & (k < W)
    return np.bincount((r * W + k)[ok], minlength=H * W).reshape(H, W), int((~ok).sum())


# ---------- de meting ----------

def wq(x, w, q):
    """Het gewogen kwantiel q van x met gewichten w."""
    if len(x) == 0 or w.sum() == 0:
        return np.nan
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][min(np.searchsorted(c, q * c[-1]), len(x) - 1)])


def fmt(v):
    return '   elke' if v == -np.inf else ('    nvt' if np.isnan(v) else f'{v:7.2f}')


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--werkkopie', type=Path, required=True, help='werkkopie van RSopen met de factoren en de pakketten')
    ap.add_argument('--variant', default='BAU', help='kolom van VariantK.dms; default BAU')
    ap.add_argument('--periode', required=True, help='beginjaar-eindjaar van de nieuwbouw, bijvoorbeeld 2012-2021')
    ap.add_argument('--voorraad', type=Path, help='woningen per cel van 25 m op 1 januari van het beginjaar; zonder dit argument uit --bag-store')
    bron = ap.add_mutually_exclusive_group(required=True)
    bron.add_argument('--nieuwbouw', type=Path, help='npz met eengezins en meergezins per cel van 25 m')
    bron.add_argument('--bag-store', type=Path, help='store van BAG-Tools, met pand.mmd en vbo.mmd')
    ap.add_argument('--rem-export', type=Path, required=True, help='map met rem_OV_100m.tif en rem_Water_100m.tif (en zonder --kernbuffers de kernklassen)')
    ap.add_argument('--kernbuffers', type=Path, help='BaseData/PopBuffers van een run')
    ap.add_argument('--bbg', type=Path, required=True, help='BBG<jaar>_100m_Modus_<studiegebied>.tif')
    ap.add_argument('--cbs', type=Path, required=True, help='CBS-gebiedsindeling (gpkg)')
    ap.add_argument('--nvm', type=Path, required=True, help='NVM-regio per cel van 25 m (tif)')
    ap.add_argument('--contour', type=Path, required=True, help='bebouwd gebied van het beginjaar (npy, tif of vlakken)')
    ap.add_argument('--uitvoer', type=Path, required=True, help='map voor de tabel')
    ap.add_argument('--aandeel', type=float, default=0.9, help='het aandeel van de nieuwe woningen dat onder de rem moet blijven; default 0.9')
    a = ap.parse_args(argv)

    m = re.fullmatch(r'(\d{4})-(\d{4})', a.periode)
    if not m or int(m.group(1)) > int(m.group(2)):
        stop(f'--periode {a.periode}: verwacht beginjaar-eindjaar, zoals 2012-2021')
    begin, eind = int(m.group(1)), int(m.group(2))
    if a.voorraad is None and a.bag_store is None:
        stop('geef --voorraad, of --bag-store om de voorraad van het beginjaar te tellen')
    if not 0 < a.aandeel < 1:
        stop('--aandeel ligt tussen 0 en 1')
    a.uitvoer.mkdir(parents=True, exist_ok=True)
    kop, uit = [], []

    def p(*t):
        s = ' '.join(str(x) for x in t)
        print(s, flush=True)
        uit.append(s)

    # ---------- de werkkopie: factoren, pakketten en de vorm van de rem ----------
    STAND = factoren(a.werkkopie, a.variant)
    pk = pakketten(a.werkkopie)
    wonen = lees_cfg(a.werkkopie, WONEN)
    vorm_eg, vorm_mg, vorm_hoog = (getal(wonen, n, WONEN) for n in ('VormfactorEengezins', 'VormfactorMeergezins', 'VormfactorHoogbouw'))
    laaghoogte, hoogbouwgrens = getal(wonen, 'Bouwlaaghoogte', WONEN), getal(wonen, 'Hoogbouwgrens', WONEN)
    straal = gladstraal(a.werkkopie)

    # pakketdichtheid zoals OPTabel_T: FSI * 10.000 * vormfactor / woonoppervlak; de vormfactor van hoogbouw geldt voor een
    # meergezinspakket waarvan FSI / GSI bouwlagen hoger reiken dan de hoogbouwgrens
    DENS = np.array([q['fsi'] * M2_PER_HA * (vorm_eg if q['eg'] else (vorm_hoog if q['fsi'] / q['gsi'] * laaghoogte > hoogbouwgrens else vorm_mg)) / q['opp']
                     for q in pk])
    SUBI = np.array([SUBS.index(('eengezins' if q['eg'] else 'meergezins') + '_' + ('VrijeSector' if q['vs'] else 'SocialeHuur')) for q in pk])
    WP2 = np.array([0 if q['eg'] else 1 for q in pk])
    RIJ = np.array([q['wp4'] == 'rijtjeswoning' for q in pk])
    MINIMUM, KERNRAND = np.zeros(4), np.zeros(4)
    for s in range(4):
        sub = SUBI == s
        if not sub.any():
            stop(f'geen pakket voor {SUBS[s]} in {PAKKETTEN}')
        MINIMUM[s] = DENS[sub].min()
        KERNRAND[s] = max(MINIMUM[s], DENS[sub & RIJ].min()) if (sub & RIJ).any() else MINIMUM[s]
    MAXCEL = [float((DENS[WP2 == t] * CEL_HA).max()) for t in (0, 1)]

    kop.append(f'IJking van de dichtheidsrem aan de echte nieuwbouw {begin}-{eind} (batch/IjkDichtheidsrem.py)')
    kop.append(f'werkkopie: {a.werkkopie.resolve()} ({commit(a.werkkopie)}), variant {a.variant}, {len(pk)} pakketten uit Default_src.dms')
    for typ, _ in TYPEN:
        kop.append(f'factoren {typ}: ' + ', '.join(f'{k} {v:.2f}' for k, v in STAND[typ].items()))
    p('ondergrens per subsector, elders / aan de kernrand (woningen per ha): ' + ', '.join(f'{SUBS[s]} {MINIMUM[s]:.2f} / {KERNRAND[s]:.2f}' for s in range(4)))
    p(f'het meeste woningen per cel van 25 m dat een pakket geeft: eengezins {MAXCEL[0]:.2f}, meergezins {MAXCEL[1]:.2f}')

    # ---------- de bouwstenen van de rem ----------
    E = {n: lees_kaart(a.rem_export / EXPORT.format(naam=n), CEL * BLOK, H1, W1, np.float64) for n in ('OV', 'Water')}
    if a.kernbuffers:
        E.update(kernbuffers(a.kernbuffers))
        kop.append(f'opslag OV en water: {a.rem_export.resolve()}; kernklassen: {a.kernbuffers.resolve()}')
    else:
        E.update({k: lees_kaart(a.rem_export / EXPORT.format(naam=k), CEL * BLOK, H1, W1, np.float64) for k, _, _, _ in KLASSEN})
        kop.append(f'opslag OV en water en de kernklassen: {a.rem_export.resolve()}')
    woon = lees_kaart(a.bbg, CEL * BLOK, H1, W1, np.int32) == WOONTERREIN
    kop.append(f'woonlocatie: {a.bbg.resolve()}; regio\'s: {a.cbs.resolve()} en {a.nvm.resolve()}; bebouwd gebied {begin}: {a.contour.resolve()}')

    REG = []
    for laag in CBS_LAGEN:
        d = pyogrio.read_dataframe(a.cbs, layer=laag).reset_index(drop=True)
        REG.append(features.rasterize(((g, i + 1) for i, g in enumerate(d.geometry)), out_shape=(H1, W1), transform=TR1, fill=0, dtype='int32'))
        if laag == PROVINCIE_LAAG:
            onbekend = [n for n in DEELGEBIED[2] if n not in set(d['statnaam'])]
            if onbekend:
                stop(f'provincie {onbekend} niet in laag {laag} van {a.cbs}')
            DEEL = np.isin(REG[-1], [i + 1 for i, n in enumerate(d['statnaam']) if n in DEELGEBIED[2]])
    v = lees_kaart(a.nvm, CEL, H, W, np.int64, vul=-1)[NVM_CEL_IN_BLOK::BLOK, NVM_CEL_IN_BLOK::BLOK]
    REG.append(np.where((v >= 0) & (v < GEODMS_NULL_UINT32), v + 1, 0).astype(np.int32))
    del v

    # de voorraad van het beginjaar
    bouwjaar_max = int(getal(lees_cfg(a.werkkopie, MODELPARAMETERS), 'BAG_RecentYear', MODELPARAMETERS)) if a.bag_store else None
    if a.voorraad:
        w0 = blok(lees_kaart(a.voorraad, CEL, H, W, np.float32))
        kop.append(f'voorraad {begin}: {a.voorraad.resolve()}')
    else:
        meld(f'woningen in de jaarset van 1 januari {begin} uit {a.bag_store} ...')
        x, y, _, _ = woon_vbos(a.bag_store, eerste_januari(begin), bouwjaar_max)
        g, buiten = naar_grid(x, y)
        w0 = blok(g.astype(np.float32))
        del x, y, g
        kop.append(f'voorraad {begin}: de woon-vbo\'s in de jaarset van 1 januari {begin} in {a.bag_store.resolve()} ({buiten:,} buiten het grid)')

    # het omgevingsmaximum: het hoogste van de eigen dichtheid en het gemiddelde over de woonblokken per regio
    D = np.where(woon, w0, np.nan)
    M = D.copy()
    for ids in REG:
        s_ = np.bincount(ids[woon], weights=D[woon], minlength=ids.max() + 1)
        n_ = np.bincount(ids[woon], minlength=ids.max() + 1)
        gem = np.where(n_ > 0, s_ / np.maximum(n_, 1), np.nan)
        gem[0] = np.nan
        M = np.fmax(M, gem[ids])
    M = np.nan_to_num(M)
    del D, REG, w0

    # gladgestreken met de kegel van MaxWoningDichtheid_T (Geography/Distmatrices, rev_dist_scaled gedeeld door zijn som)
    nk = int(straal // (CEL * BLOK))
    d = np.arange(-nk, nk + 1) * (CEL * BLOK)
    KEGEL = np.clip(straal - np.hypot(d[:, None], d[None, :]), 0, None)
    KEGEL /= KEGEL.sum()

    def glad(x):
        return fftconvolve(x, KEGEL, mode='same')

    S0 = glad(M)
    S = {n: glad(M * E[n]) for n in E}
    B0 = blok(contour(a.contour).astype(np.float32)) >= BINNEN_MIN_CELLEN
    KL = np.full((H1, W1), -1)
    for i, (k, _, _, _) in enumerate(KLASSEN):
        KL[(KL < 0) & (E[k] >= DEKKING_KERNKLASSE)] = i
    KERN = np.minimum(sum(E[k] for k, _, _, _ in KLASSEN), 1.0)
    OG = [KERN * KERNRAND[s] + (1 - KERN) * MINIMUM[s] for s in range(4)]

    def rem_stand(st):
        return S0 * st['gen'] + (st['ov'] - 1) * S['OV'] + (st['water'] - 1) * S['Water'] + sum((st[k] - 1) * S[k] for k, _, _, _ in KLASSEN)

    # ---------- de nieuwbouw per type ----------
    if a.bag_store:
        meld(f'nieuwbouw in de jaarset van 1 januari {eind + 1} met een bouwjaar vanaf {begin} uit {a.bag_store} ...')
        x, y, t, bj = woon_vbos(a.bag_store, eerste_januari(eind + 1), bouwjaar_max)
        nieuw = bj >= begin
        x, y, t = x[nieuw], y[nieuw], t[nieuw]
        per_type = {naam: naar_grid(x[t == c], y[t == c])[0] for naam, c in (('eengezins', 1), ('meergezins', 2), ('zonder_type', 0))}
        del x, y, t, bj, nieuw
        npz = a.uitvoer / f'bag_nieuw_{begin}_{eind}_per_type.npz'
        dt = np.uint16 if max(int(v.max()) for v in per_type.values()) < np.iinfo(np.uint16).max else np.uint32
        np.savez_compressed(npz, **{k: v.astype(dt) for k, v in per_type.items()})
        kop.append(f'nieuwbouw: de woon-vbo\'s in de jaarset van 1 januari {eind + 1} met een bouwjaar vanaf {begin} in {a.bag_store.resolve()} '
                   f'(BAG_RecentYear {bouwjaar_max}; {int(per_type["zonder_type"].sum()):,} zonder type), bewaard in {npz.name}')
    else:
        per_type = np.load(a.nieuwbouw)
        kop.append(f'nieuwbouw: {a.nieuwbouw.resolve()}')
    X = []
    for typ, _ in TYPEN:
        kaart = per_type[typ] if typ in per_type else None
        if kaart is None or kaart.shape != (H, W):
            stop(f'de nieuwbouw heeft geen kaart {typ} van {H} bij {W} cellen')
        X.append(blok(kaart.astype(np.float32)).astype(np.float64))
        del kaart
    del per_type
    MAJ = [(X[0] >= MIN_NIEUW_BLOK) & (X[0] >= X[1]), (X[1] >= MIN_NIEUW_BLOK) & (X[1] > X[0])]
    p(f'nieuwe woningen {begin}-{eind}: eengezins {X[0].sum():,.0f}, meergezins {X[1].sum():,.0f}; waarvan in {DEELGEBIED[1]} '
      f'{X[0][DEEL].sum():,.0f} en {X[1][DEEL].sum():,.0f}')

    # ---------- de tabel ----------
    pct = f'{a.aandeel * 100:.0f} procent'
    p(f'\n== Factor voor de kerngrootte waarbij {pct} van de nieuwe woningen van het type onder de rem blijft, zonder en met de ondergrens')
    p(f'   blokken waar het type de meerderheid heeft; binnen = bebouwd gebied {begin}; "elke": {pct} blijft al onder de ondergrens, bij elke factor')
    p('   onder OG: aandeel van de woningen op blokken met een dichtheid onder de ondergrens (die komen bij elke factor door)')
    p(f'{"type":11s} {"ondergrens":12s} {"gebied":7s} {"kernen":20s} {"ligging":7s} {"woningen":>9s} {"stand":>6s} | {"zonder OG: onder rem":>20s} {"ijkwaarde":>9s} | '
      f'{"onder OG":>8s} {"met OG: onder rem":>17s} {"ijkwaarde":>9s}')
    alles = np.ones((H1, W1), bool)
    for t, (typ, _) in enumerate(TYPEN):
        st = STAND[typ]
        basis = rem_stand(st)
        for og_naam, s in [('vrije sector', 2 * t), ('sociale huur', 2 * t + 1)]:
            og = OG[s]
            for gnaam, gm in [('NL', alles), (DEELGEBIED[0], DEEL)]:
                for i, (k, kn, _, _) in enumerate(KLASSEN):
                    rest = basis - (st[k] - 1) * S[k]
                    for lbl, lm in [('binnen', B0), ('buiten', ~B0), ('samen', alles)]:
                        sel = MAJ[t] & (KL == i) & lm & gm & (S[k] > MIN_KERNGEWICHT)
                        x = X[t][sel]
                        if x.sum() == 0:
                            p(f'{typ:11s} {og_naam:12s} {gnaam:7s} {kn:20s} {lbl:7s} {0:9,.0f} {st[k]:6.2f} | {"nvt":>20s} {"nvt":>9s} | {"nvt":>8s} {"nvt":>17s} {"nvt":>9s}')
                            continue
                        f = 1 + (x - rest[sel]) / S[k][sel]
                        onder_og = x <= og[sel]
                        f_og = np.where(onder_og, -np.inf, f)
                        door0 = x[f <= st[k]].sum() / x.sum()
                        door1 = x[(f <= st[k]) | onder_og].sum() / x.sum()
                        p(f'{typ:11s} {og_naam:12s} {gnaam:7s} {kn:20s} {lbl:7s} {x.sum():9,.0f} {st[k]:6.2f} | {door0:20.2f} {fmt(wq(f, x, a.aandeel)):>9s} | '
                          f'{x[onder_og].sum() / x.sum():8.2f} {door1:17.2f} {fmt(wq(f_og, x, a.aandeel)):>9s}')

    pad = a.uitvoer / f'IjkDichtheidsrem_{begin}_{eind}.txt'
    pad.write_text('\n'.join(kop + [''] + uit) + '\n', encoding='utf-8')
    meld(f'\ntabel: {pad}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
