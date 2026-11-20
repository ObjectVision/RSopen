# Waar ligt het bouwterrein dat binnen de BBG-reeks terugviel naar agrarisch, en hoe verhoudt dat zich tot de daling 2015-2017.
# Gebruik: python bbg_terugagrarisch.py <mutatie1996_2017.gpkg> <cbsgebiedsindelingen2017.gpkg> <uitmap>
import sys, os, sqlite3
import pandas as pd, geopandas as gpd, pyogrio, shapely
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

BBG, GEM, UIT = sys.argv[1:4]
AGR = (50, 51)
con = sqlite3.connect(f"file:{BBG}?immutable=1", uri=True)
tot = pd.read_sql("select sum(case when BG15 = 34 then Shape_Area end)/1e4 h15, sum(case when BG17 = 34 then Shape_Area end)/1e4 h17, "
                  "sum(case when BG15 = 34 and BG17 in (50, 51) then Shape_Area end)/1e4 agr, "
                  "sum(case when BG15 = 34 and BG17 <> 34 then Shape_Area end)/1e4 uit, "
                  "sum(case when BG15 <> 34 and BG17 = 34 then Shape_Area end)/1e4 nieuw from CBS_MutatiebestandBBG1996_2017_v1", con).iloc[0]
daling = tot.h15 - tot.h17
print(f"bouwterrein 2015 {tot.h15:.0f} ha, 2017 {tot.h17:.0f} ha, netto daling {daling:.0f} ha; uitstroom {tot.uit:.0f} ha, "
      f"waarvan naar agrarisch {tot.agr:.0f} ha ({100*tot.agr/tot.uit:.0f}% van de uitstroom, {100*tot.agr/daling:.0f}% van de netto daling); "
      f"nieuw bouwterrein {tot.nieuw:.0f} ha")

v = pyogrio.read_dataframe(BBG, where="BG12 = 34 and BG17 in (50, 51)", columns=["BG08", "BG10", "BG15"])
v["geometry"] = shapely.force_2d(v.geometry.values)
v["ha"] = v.area / 1e4
g = pyogrio.read_dataframe(GEM, layer="gemeente_gegeneraliseerd")
naam = [k for k in g.columns if "naam" in k.lower()][0]
p = gpd.GeoDataFrame(v[["ha"]], geometry=v.geometry.representative_point(), crs=v.crs)
j = gpd.sjoin(p, g[[naam, "geometry"]].to_crs(v.crs), how="left", predicate="within")
top = j.groupby(naam).ha.sum().sort_values(ascending=False)
print(f"bouwterrein 2012 dat in 2017 agrarisch is: {v.ha.sum():.0f} ha in {len(v)} vlakken; vlakken groter dan 10 ha: {100*v.ha[v.ha > 10].sum()/v.ha.sum():.0f}% van de oppervlakte")
print("top 15 gemeenten (ha):"); print(top.head(15).round(0).to_string())
print(f"aandeel top 15: {100*top.head(15).sum()/top.sum():.0f}%")
os.makedirs(UIT, exist_ok=True)
top.round(1).to_csv(os.path.join(UIT, "bouwterrein2012_naar_agrarisch2017_gemeente.csv"), sep=";", decimal=",")

fig, ax = plt.subplots(figsize=(6, 7), dpi=200)
g.to_crs(v.crs).boundary.plot(ax=ax, color="#cccccc", lw=0.3)
v.plot(ax=ax, color="#c0392b", edgecolor="#c0392b", lw=0.6)
ax.set_axis_off()
ax.set_title("Bouwterrein in 2012 dat in 2017 weer agrarisch is", fontsize=11, loc="left")
ax.text(0.0, -0.02, "Bron: CBS, mutatiebestand BBG 1996–2017", transform=ax.transAxes, fontsize=7, color="#555555")
fig.savefig(os.path.join(UIT, "bouwterrein2012_naar_agrarisch.png"), bbox_inches="tight")
