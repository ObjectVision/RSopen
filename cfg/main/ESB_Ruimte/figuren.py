"""Tekent de figuren van de ESB-analyses A en B als png uit de csv's die GeoDMS schrijft
(ESB_Ruimte/WerkenPerBaan en ESB_Ruimte/WaardePerM2). Alleen presentatie: elk getal komt uit die csv's.

Gebruik: python figuren.py <map met de csv's>   (schrijft ESB_A*.png en ESB_B*.png in dezelfde map)
"""
import sys
from pathlib import Path

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
}
# Vaste volgorde per sector, getoetst op kleurenblindheid (dataviz validate_palette, licht).
KLEUR = dict(zip(SECTOREN, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]))
INKT, INKT2, RASTER, ACHTERGROND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Segoe UI", "Arial", "sans-serif"], "font.size": 11, "axes.edgecolor": INKT2,
    "axes.labelcolor": INKT2, "xtick.color": INKT2, "ytick.color": INKT2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": RASTER, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.facecolor": ACHTERGROND, "axes.facecolor": ACHTERGROND,
    "savefig.facecolor": ACHTERGROND, "legend.frameon": False,
})


def nl(x, dec=0):
    """Een getal met punt voor duizendtallen, komma voor decimalen en een echt minteken."""
    return f"{x:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".").replace("-", "\u2212")


def as_getal(dec=None):
    """Een asformatter; zonder dec alleen decimalen waar de streep geen geheel getal is."""
    return FuncFormatter(lambda v, _: nl(v, dec if dec is not None else (0 if float(v).is_integer() else 1)))


def lees(pad):
    df = pd.read_csv(pad)
    df.columns = [c.lower() for c in df.columns]
    return df


def kop(fig, titel, ondertitel):
    fig.text(0.02, 0.975, titel, fontsize=14, fontweight="bold", color=INKT, va="top")
    fig.text(0.02, 0.915, ondertitel, fontsize=10.5, color=INKT2, va="top")


def legenda(ax, n_kol=2):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=n_kol, fontsize=10, handlelength=1.6,
              columnspacing=1.2, borderaxespad=0.3)


def lijnen(df, kolom, titel, ondertitel, uit, deler=1.0, dec=0, jaren=None, y0=True):
    fig, ax = plt.subplots(figsize=(6.4, 5.0), dpi=200)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.70, bottom=0.09)
    kop(fig, titel, ondertitel)
    for s, lab in SECTOREN.items():
        d = df[(df.sector == s) & df[kolom].notna()]
        if jaren:
            d = d[d.jaar.between(*jaren)]
        ax.plot(d.jaar, d[kolom] / deler, color=KLEUR[s], lw=2, label=lab)
    if y0:
        ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(as_getal(dec))
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True, nbins=7))
    legenda(ax)
    fig.savefig(uit)
    plt.close(fig)


def ontleding(df, uit):
    df = df.set_index("sector").loc[list(SECTOREN)]
    fig, ax = plt.subplots(figsize=(6.4, 5.0), dpi=200)
    fig.subplots_adjust(left=0.36, right=0.95, top=0.74, bottom=0.11)
    kop(fig, "Groei van de voetafdruk 2012–2023 ontleed",
        "miljoen m², deel door meer banen en deel door\nmeer of minder m² per baan")
    y = range(len(df))
    h = 0.38
    ax.barh([i - h / 2 for i in y], df.door_banen_m2 / 1e6, height=h, color=KLEUR["Nijverheid"], label="door meer banen")
    ax.barh([i + h / 2 for i in y], df.door_m2baan_m2 / 1e6, height=h, color=KLEUR["Logistiek"], label="door m² per baan")
    ax.set_yticks(list(y), [SECTOREN[s] for s in df.index])
    ax.invert_yaxis()
    ax.axvline(0, color=INKT2, lw=0.8)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(as_getal())
    legenda(ax)
    fig.savefig(uit)
    plt.close(fig)


def staven(waarden, titel, ondertitel, uit, dec=0):
    waarden = waarden.sort_values()
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
    fig.subplots_adjust(left=0.36, right=0.88, top=0.80, bottom=0.08)
    kop(fig, titel, ondertitel)
    ax.barh([SECTOREN[s] for s in waarden.index], waarden, color=KLEUR["Nijverheid"], height=0.6)
    for i, v in enumerate(waarden):
        ax.text(v, i, " " + nl(v, dec), va="center", fontsize=10, color=INKT)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(as_getal())
    fig.savefig(uit)
    plt.close(fig)


def main(map_):
    map_ = Path(map_)
    werk = lees(map_ / "WerkenPerBaan_reeks.csv")
    ontl = lees(map_ / "WerkenPerBaan_ontleding.csv")
    waarde = lees(map_ / "WaardePerM2_reeks.csv")
    laatste_lisa = int(werk[werk.m2_per_baan.notna()].jaar.max())

    lijnen(werk, "m2_per_baan", "Pandvoetafdruk per baan",
           f"m² per LISA-baan, 2012–{laatste_lisa}", map_ / "ESB_A1_m2_per_baan.png", jaren=(2012, laatste_lisa))
    lijnen(werk, "banen", "Banen per sector", f"miljoen LISA-banen, 1996–{laatste_lisa}",
           map_ / "ESB_A2_banen.png", deler=1e6, dec=1)
    lijnen(werk, "voetafdruk_m2", "Pandvoetafdruk per sector",
           "km², BAG op 1 januari", map_ / "ESB_A3_voetafdruk.png", deler=1e6)
    ontleding(ontl, map_ / "ESB_A4_ontleding.png")

    w = waarde[waarde.jaar == waarde.jaar.max()].set_index("sector")
    jaar = int(waarde.jaar.max())
    staven(w.euro_per_m2, "Toegevoegde waarde per m² voetafdruk", f"euro per m², {jaar}",
           map_ / "ESB_B1_euro_per_m2.png")
    staven(w.euro_per_baan / 1000, "Toegevoegde waarde per baan", f"duizend euro per LISA-baan, {jaar}",
           map_ / "ESB_B2_euro_per_baan.png")
    basis = waarde[waarde.jaar == waarde.jaar.min()].set_index("sector").euro2021_per_m2
    waarde["index_m2"] = 100 * waarde.euro2021_per_m2 / waarde.sector.map(basis)
    lijnen(waarde, "index_m2", "Toegevoegde waarde per m² in prijzen van 2021",
           f"prijsniveau 2021, index {int(waarde.jaar.min())} = 100", map_ / "ESB_B3_index_m2.png", y0=False)
    print("figuren in", map_)


if __name__ == "__main__":
    main(sys.argv[1])
