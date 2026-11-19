"""Tekent de figuur van taak E (werk naar wonen) uit de csv's die GeoDMS schrijft (ESB_Ruimte/WerkNaarWonen) en de
CBS-reeks uit data/CBS_transformatie (ophalen.py haalt de tabellen, tabel.py maakt de csv). Alleen presentatie: elk getal komt uit die csv's.

Gebruik: python figuren_WerkNaarWonen.py <map met de GeoDMS-csv's> <cbs_transformatie_NL.csv> <uit.png>
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

SECTOREN = {
    "Nijverheid": "Nijverheid",
    "Logistiek": "Logistiek",
    "Detailhandel": "Detailhandel",
    "Ov_consumentendiensten": "Ov. consumentendiensten",
    "Zak_dienstverlening": "Zakelijke dienstverlening",
    "Overheid_kw_diensten": "Overheid en kw. diensten",
    "onbekend": "Onbekend",
}
# Dezelfde sectorkleuren als figuren.py van het dossier, plus grijs voor onbekend.
KLEUR = dict(zip(SECTOREN, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#a9a8a3"]))
INKT, INKT2, RASTER, ACHTERGROND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Segoe UI", "Arial", "sans-serif"], "font.size": 11, "axes.edgecolor": INKT2,
    "axes.labelcolor": INKT2, "xtick.color": INKT2, "ytick.color": INKT2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": RASTER, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.facecolor": ACHTERGROND, "axes.facecolor": ACHTERGROND,
    "savefig.facecolor": ACHTERGROND, "legend.frameon": False,
})


def nl(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".").replace("-", "−")


def lees(pad):
    df = pd.read_csv(pad)
    df.columns = [c.lower() for c in df.columns]
    return df


def main(map_, cbs_pad, uit):
    sector = lees(f"{map_}/WerkNaarWonen_sector.csv")
    heen = lees(f"{map_}/WerkNaarWonen_totaal.csv")
    terug = lees(f"{map_}/WonenNaarWerken_totaal.csv")
    cbs = lees(cbs_pad)
    # 2020 tot en met 2022 staan in beide CBS-tabellen; neem de nieuwste.
    cbs = cbs.sort_values(["jaar", "tabel"]).drop_duplicates("jaar", keep="last").set_index("jaar")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, 9.6), dpi=200, gridspec_kw={"height_ratios": [1.35, 1]})
    fig.subplots_adjust(left=0.13, right=0.97, top=0.79, bottom=0.06, hspace=0.42)
    fig.text(0.02, 0.985, "Werkpanden die woningen werden", fontsize=14, fontweight="bold", color=INKT, va="top")
    fig.text(0.02, 0.955, "Woningen per jaar uit werkfuncties, naar de sector van\nde vorige functie; BAG per 1 januari, Nederland", fontsize=10.5,
             color=INKT2, va="top")

    tab = sector.pivot(index="jaar", columns="sector", values="woningen").fillna(0)
    onder = pd.Series(0.0, index=tab.index)
    for s, lab in SECTOREN.items():
        if s in tab and tab[s].sum() > 0:
            a1.bar(tab.index, tab[s], bottom=onder, color=KLEUR[s], width=0.75, label=lab)
            onder += tab[s]
    jaren = tab.index
    a1.plot(jaren, cbs.reindex(jaren)["transformatie"], color=INKT, lw=2, marker="o", ms=3.5,
            label="CBS transformatie")
    a1.plot(jaren, cbs.reindex(jaren)["transformatie"] + cbs.reindex(jaren)["overig_naar_woon"], color=INKT, lw=1.4,
            ls="--", label="CBS idem + functiewijziging")
    a1.set_ylabel("woningen")
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: nl(v)))
    a1.set_xticks(list(jaren)[::2])
    a1.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=9, handlelength=1.4, columnspacing=1.0)

    a2.plot(heen.jaar, heen.woningen, color=KLEUR["Nijverheid"], lw=2, marker="o", ms=3.5, label="werken naar wonen")
    a2.plot(terug.jaar, terug.woningen, color=KLEUR["Logistiek"], lw=2, marker="o", ms=3.5, label="wonen naar werken")
    a2.set_ylabel("woningen")
    a2.set_ylim(bottom=0)
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: nl(v)))
    a2.set_xticks(list(heen.jaar)[::2])
    a2.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=9.5)
    a2.set_title("Beide richtingen", loc="left", fontsize=10.5, color=INKT2, pad=26)
    fig.text(0.02, 0.012, "Mutatiejaar: van 1 januari tot 1 januari erna. Bron: BAG (bewerking RSopen), CBS 84903NED en 86054NED.",
             fontsize=8, color=INKT2)
    fig.savefig(uit)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
