# Wat werd het BBG-bouwterrein van 2012 (en 2015) in latere jaargangen?
# Deel 1 uit de attribuuttabel van het mutatiebestand 1996-2017 (elk vlak heeft de klasse van elk jaar).
# Deel 2 een geometrische overlay van het bouwterrein van 2012 met de NBBG 2020 en 2022 (andere geometrie, methodebreuk).
# Gebruik: python -I bbg_overgang.py <mutatie1996_2017.gpkg> <nbbg2022.gpkg> <uitmap>
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

con = sqlite3.connect(f"file:{BBG}?immutable=1", uri=True)
df = pd.read_sql("select BG08, BG10, BG12, BG15, BG17, Shape_Area from CBS_MutatiebestandBBG1996_2017_v1 "
                 "where BG12 = 34 or BG15 = 34", con)
df["ha"] = df.Shape_Area / 1e4

tab = {}
for van, naar in [("BG12", "BG15"), ("BG12", "BG17"), ("BG15", "BG17")]:
    d = df[df[van] == 34]
    tab[f"{van[2:]}->{naar[2:]}"] = d.groupby(d[naar].map(groep)).ha.sum()

# Hoe lang lag het bouwterrein van 2012 al stil: in hoeveel van de jaargangen 2008, 2010 en 2012 was het bouwterrein.
d12 = df[df.BG12 == 34].copy()
d12["sinds"] = np.where(d12.BG08 == 34, "al in 2008", np.where(d12.BG10 == 34, "sinds 2010", "nieuw in 2012"))
sinds = d12.pivot_table(index="sinds", columns=d12.BG17.map(groep), values="ha", aggfunc="sum", fill_value=0)

# Deel 2: overlay met de NBBG.
b12 = pyogrio.read_dataframe(BBG, where="BG12 = 34", columns=["BG12"])
b12["geometry"] = shapely.force_2d(b12.geometry.values)
b12 = b12[["geometry"]]
lnaam = "cbs_mutatiebestand_nbbg2022_v1_def_undissolved"
c2 = sqlite3.connect(f"file:{NBBG}?immutable=1", uri=True)
rt = pd.read_sql(f'select id, minx, maxx, miny, maxy from "rtree_{lnaam}_geom"', c2)
xmin, ymin, xmax, ymax = b12.total_bounds
boom = shapely.STRtree(b12.geometry.values)
kand = boom.query(shapely.box(rt.minx, rt.miny, rt.maxx, rt.maxy), predicate="intersects")
fids = np.unique(rt.id.values[kand[0]])
nb = pyogrio.read_dataframe(NBBG, layer=lnaam, fids=fids, columns=["NBBG20", "NBBG22"])
nb["geometry"] = shapely.force_2d(nb.geometry.values)
nb = nb.set_crs(b12.crs, allow_override=True)
ov = gpd.overlay(b12, nb, how="intersection", keep_geom_type=True)
ov["ha"] = ov.area / 1e4
for k in ("NBBG20", "NBBG22"):
    tab[f"12->{k[-2:]} (NBBG)"] = ov.groupby(ov[k].map(groep)).ha.sum()
print("overig:", ov[ov.NBBG22.map(groep) == "Overig"].groupby("NBBG22").ha.sum().round(0).to_dict())
dek = ov.ha.sum() / (b12.area.sum() / 1e4)

t = pd.DataFrame(tab).reindex(VOLG).fillna(0)
t.loc["Totaal"] = t.sum()
pct = 100 * t / t.loc["Totaal"]
os.makedirs(UIT, exist_ok=True)
t.round(0).to_csv(os.path.join(UIT, "bouwterrein_overgang_ha.csv"), sep=";", decimal=",")
pct.round(1).to_csv(os.path.join(UIT, "bouwterrein_overgang_pct.csv"), sep=";", decimal=",")
sinds.round(0).to_csv(os.path.join(UIT, "bouwterrein2012_sinds.csv"), sep=";", decimal=",")
pd.set_option("display.width", 250)
print(t.round(0)); print(pct.round(1)); print(sinds.round(0)); print(f"dekking overlay NBBG: {dek:.4f}")
