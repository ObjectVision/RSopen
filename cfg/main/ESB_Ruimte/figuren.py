"""Tekent de figuren van de ESB-analyses als svg uit de csv's die GeoDMS schrijft (ESB_Ruimte/WerkenPerBaan
en ESB_Ruimte/WaardePerM2). Alleen presentatie: elk getal komt uit die csv's. Zonder externe packages.

Gebruik: python figuren.py <map met de csv's>   (schrijft ESB_figuren.svg in dezelfde map)
"""
import csv
import math
import sys
from pathlib import Path

LABEL = {
    "Nijverheid": "Nijverheid",
    "Logistiek": "Logistiek",
    "Detailhandel": "Detailhandel",
    "Ov_consumentendiensten": "Ov. consumentendiensten",
    "Zak_dienstverlening": "Zakelijke dienstverlening",
    "Overheid_kw_diensten": "Overheid en kw. diensten",
}
KLEUR = dict(zip(LABEL, ["#1f4e79", "#2e86c1", "#c0392b", "#e67e22", "#7d3c98", "#27ae60"]))
B, H = 640, 400          # breedte en hoogte van een paneel
L, R, T, O = 60, 20, 40, 40  # marges links, rechts, boven, onder


def lees(pad):
    return [{k.lower(): v for k, v in r.items()} for r in csv.DictReader(open(pad, encoding="utf-8"))]


def reeks(rijen, kolom, deler=1.0):
    uit = {}
    for r in rijen:
        if r[kolom] not in ("", None):
            uit.setdefault(r["sector"], []).append((int(r["jaar"]), float(r[kolom]) / deler))
    return uit


def paneel(y0, titel, data, log=False, x_bereik=None):
    xs = [x for v in data.values() for x, _ in v]
    ys = [y for v in data.values() for _, y in v]
    x0, x1 = x_bereik or (min(xs), max(xs))
    if log:
        lo, hi = 500.0 if min(ys) >= 500 else 10 ** math.floor(math.log10(min(ys))), 10 ** math.ceil(math.log10(max(ys)))
        f = lambda y: math.log10(y)
        y_lo, y_hi = f(lo), f(hi)
        ticks = [10 ** e * m for e in range(int(y_lo), int(y_hi)) for m in (1, 2, 5)] + [hi]
    else:
        y_lo, y_hi = 0.0, max(ys) * 1.08
        stap = 10 ** math.floor(math.log10(y_hi / 5))
        stap *= 2 if y_hi / stap > 10 else 1
        f = lambda y: y
        ticks = [i * stap for i in range(int(y_hi / stap) + 1)]
    dec = 0 if log else max(0, -math.floor(math.log10(stap)))
    px = lambda x: L + (x - x0) / (x1 - x0) * (B - L - R)
    py = lambda y: y0 + T + (1 - (f(y) - y_lo) / (y_hi - y_lo)) * (H - T - O)
    s = [f'<text x="{L}" y="{y0 + 24}" font-size="17" font-weight="600">{titel}</text>']
    for t in ticks:
        if f(t) < y_lo or f(t) > y_hi:
            continue
        s.append(f'<line x1="{L}" x2="{B - R}" y1="{py(t):.1f}" y2="{py(t):.1f}" stroke="#ddd"/>')
        lab = f"{t:,.{dec}f}".replace(",", " ").replace(".", ",").replace(" ", ".")
        s.append(f'<text x="{L - 6}" y="{py(t) + 4:.1f}" font-size="12" text-anchor="end" fill="#555">{lab}</text>')
    for x in range(x0, x1 + 1):
        if x % 4 == 0:
            s.append(f'<text x="{px(x):.1f}" y="{y0 + H - O + 18}" font-size="12" text-anchor="middle" fill="#555">{x}</text>')
    for k, v in data.items():
        v = sorted(v)
        pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in v)
        s.append(f'<polyline points="{pts}" fill="none" stroke="{KLEUR[k]}" stroke-width="2.5"/>')
    return s


def main(map_):
    map_ = Path(map_)
    werk = lees(map_ / "WerkenPerBaan_reeks.csv")
    waarde = lees(map_ / "WaardePerM2_reeks.csv")
    hoog = 3 * H + 150
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{B}" height="{hoog}" viewBox="0 0 {B} {hoog}" font-family="Segoe UI, Arial, sans-serif">',
         f'<rect width="{B}" height="{hoog}" fill="white"/>']
    s += paneel(0, "Pandvoetafdruk per baan (m²)", reeks(werk, "m2_per_baan"), x_bereik=(2012, 2023))
    s += paneel(H, "Banen per sector, LISA (miljoen)", reeks(werk, "banen", 1e6), x_bereik=(1996, 2023))
    s += paneel(2 * H, "Toegevoegde waarde per m² voetafdruk (euro, lopende prijzen, log)", reeks(waarde, "euro_per_m2"), log=True)
    for i, (k, lab) in enumerate(LABEL.items()):
        x, y = L + (i % 2) * 290, 3 * H + 30 + (i // 2) * 26
        s.append(f'<line x1="{x}" x2="{x + 28}" y1="{y}" y2="{y}" stroke="{KLEUR[k]}" stroke-width="4"/>')
        s.append(f'<text x="{x + 36}" y="{y + 5}" font-size="14">{lab}</text>')
    s.append("</svg>")
    uit = map_ / "ESB_figuren.svg"
    uit.write_text("\n".join(s), encoding="utf-8")
    print(uit)


if __name__ == "__main__":
    main(sys.argv[1])
