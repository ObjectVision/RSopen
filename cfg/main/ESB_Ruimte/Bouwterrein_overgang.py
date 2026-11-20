# Wat wordt het BBG-bouwterrein in de volgende jaargang, en hoeveel bouwterrein komt er nieuw bij?
# Tot 2017 uit de attribuuttabel van het mutatiebestand BBG 1996-2017, waarin elk vlak de klasse van elk jaar heeft.
# Van 2017 naar 2020 een geometrische overlay met de NBBG (andere geometrie, methodebreuk); van 2020 naar 2022 de
# attribuuttabel van de NBBG. Daarnaast het cohort: wat het bouwterrein van 2012 in elke latere jaargang is.
# Gebruik: python Bouwterrein_overgang.py <mutatie1996_2017.gpkg> <nbbg2022.gpkg> <uitmap>
import sqlite3, sys, os
import pandas as pd, numpy as np, geopandas as gpd, pyogrio, shapely

BBG, NBBG, UIT = sys.argv[1:4]
GROEP = {}
for c in (20,): GROEP[c] = "Wonen"
for c in (21, 22, 23): GROEP[c] = "Voorzieningen, detailhandel en horeca"
for c in (24,): GROEP[c] = "Bedrijfsterrein"
for c in (10, 11, 12, 13): GROEP[c] = "Verkeer"
for c in (34,): GROEP[c] = "Nog bouwterrein"
for c in (35,): GROEP[c] = "Semi-verhard overig"
for c in (30, 31, 33): GROEP[c] = "Stort en delfstoffen"
for c in (32, 40, 41, 42, 43, 44): GROEP[c] = "Park, sport en recreatie"
for c in (50, 51, 52, 53): GROEP[c] = "Agrarisch"
GROEP[36] = "Zonnepark"
for c in (60, 61, 62): GROEP[c] = "Bos en natuur"
VOLG = ["Wonen", "Bedrijfsterrein", "Voorzieningen, detailhandel en horeca", "Verkeer", "Semi-verhard overig",
        "Park, sport en recreatie", "Nog bouwterrein", "Zonnepark", "Agrarisch", "Bos en natuur", "Water", "Stort en delfstoffen", "Overig"]
groep = lambda c: GROEP.get(int(c), "Water" if 70 <= int(c) <= 83 else "Overig")
BT = 34
LAAG = "cbs_mutatiebestand_nbbg2022_v1_def_undissolved"

con = sqlite3.connect(f"file:{BBG}?immutable=1", uri=True)
df = pd.read_sql("select BG10, BG12, BG15, BG17, Shape_Area from CBS_MutatiebestandBBG1996_2017_v1 "
                 "where BG10 = 34 or BG12 = 34 or BG15 = 34 or BG17 = 34", con)
df["ha"] = df.Shape_Area / 1e4


def lees_bbg(jaar):
    v = pyogrio.read_dataframe(BBG, where=f"BG{jaar % 100} = {BT}", columns=[])
    return gpd.GeoDataFrame(geometry=shapely.force_2d(v.geometry.values), crs=v.crs)


def lees_nbbg(where=None, fids=None, crs=None):
    v = pyogrio.read_dataframe(NBBG, layer=LAAG, where=where, fids=fids, columns=["NBBG20", "NBBG22"])
    v["geometry"] = shapely.force_2d(v.geometry.values)
    return v.set_crs(crs, allow_override=True) if crs is not None else v


def overlay_nbbg(vlakken):
    """De vlakken gesneden met de NBBG-vlakken die hun omhullende raken, met de klassen van 2020 en 2022."""
    c2 = sqlite3.connect(f"file:{NBBG}?immutable=1", uri=True)
    rt = pd.read_sql(f'select id, minx, maxx, miny, maxy from "rtree_{LAAG}_geom"', c2)
    kand = shapely.STRtree(vlakken.geometry.values).query(shapely.box(rt.minx, rt.miny, rt.maxx, rt.maxy), predicate="intersects")
    nb = lees_nbbg(fids=np.unique(rt.id.values[kand[0]]), crs=vlakken.crs)
    ov = gpd.overlay(vlakken, nb, how="intersection", keep_geom_type=True)
    ov["ha"] = ov.area / 1e4
    return ov


def stap(vorig, nu, ha_vorig_klasse_nu, ha_nieuw):
    """Een stap: het bouwterrein van de vorige jaargang naar zijn klasse nu, en het nieuwe bouwterrein."""
    s = ha_vorig_klasse_nu.groupby(level=0).sum()
    s.index = s.index.map(groep)
    s = s.groupby(level=0).sum()
    s["Nieuw bouwterrein"] = ha_nieuw
    return pd.DataFrame({"jaar": nu, "vorige_jaargang": vorig, "klasse": s.index, "ha": s.values})


stappen = []
for v, n in [(10, 12), (12, 15), (15, 17)]:
    d = df[df[f"BG{v}"] == BT]
    stappen.append(stap(2000 + v, 2000 + n, d.groupby(f"BG{n}").ha.sum(),
                        df[(df[f"BG{n}"] == BT) & (df[f"BG{v}"] != BT)].ha.sum()))

b17 = lees_bbg(2017)
ov17 = overlay_nbbg(b17)
nb = lees_nbbg(where=f"NBBG20 = {BT} or NBBG22 = {BT}")
nb["ha"] = nb.area / 1e4
# Nieuw in 2020: het NBBG-bouwterrein van 2020 dat buiten het BBG-bouwterrein van 2017 valt.
nieuw20 = nb[nb.NBBG20 == BT].ha.sum() - ov17[ov17.NBBG20 == BT].ha.sum()
stappen.append(stap(2017, 2020, ov17.groupby("NBBG20").ha.sum(), nieuw20))
d = nb[nb.NBBG20 == BT]
stappen.append(stap(2020, 2022, d.groupby("NBBG22").ha.sum(), nb[(nb.NBBG22 == BT) & (nb.NBBG20 != BT)].ha.sum()))
st = pd.concat(stappen)
st["klasse"] = st.klasse.replace({"Nog bouwterrein": "Bleef bouwterrein"})

# Het cohort van 2012: in 2012 alles bouwterrein, daarna de klasse in elke latere jaargang.
d12 = df[df.BG12 == BT]
ov12 = overlay_nbbg(lees_bbg(2012))
coh = {2012: pd.Series({"Nog bouwterrein": d12.ha.sum()})}
for j in (15, 17):
    coh[2000 + j] = d12.groupby(d12[f"BG{j}"].map(groep)).ha.sum()
for k in ("NBBG20", "NBBG22"):
    coh[2000 + int(k[-2:])] = ov12.groupby(ov12[k].map(groep)).ha.sum()
coh = pd.DataFrame(coh).fillna(0).rename_axis("klasse").reset_index().melt(id_vars="klasse", var_name="jaar", value_name="ha")
coh["vorige_jaargang"] = 2012

os.makedirs(UIT, exist_ok=True)
st.insert(0, "reeks", "volgende jaargang")
coh.insert(0, "reeks", "cohort 2012")
uit = pd.concat([st, coh[st.columns[:]]])
uit[["reeks", "jaar", "vorige_jaargang", "klasse", "ha"]].round(1).to_csv(os.path.join(UIT, "Bouwterrein_overgang_BBG.csv"), index=False)
pd.set_option("display.width", 250)
print(st.pivot_table(index="klasse", columns="jaar", values="ha", aggfunc="sum").round(0))
print("dekking overlay 2017:", round(ov17.ha.sum() / (b17.area.sum() / 1e4), 4), " 2012:", round(ov12.ha.sum() / (d12.ha.sum()), 4))
