"""Kaart van het BBG-bouwterrein per jaargang uit Bouwterrein_kaart_100m.csv (ESB_Ruimte/Bouwterrein): per cel van 100 meter
blauw waar het bouwterrein binnen Zoekstraal van een pand uit de pijplijn ligt, oranje waar niet. Toetst ook dat de som per
jaar gelijk is aan Ha_raster in Bouwterrein_overlay_BBG.csv. Alleen presentatie: elk getal komt uit die csv's.

Gebruik: python figuren_Bouwterrein.py <map met de csv's>   (schrijft Bouwterrein_kaart.png in dezelfde map)
"""
import pathlib
import sys

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

BLAUW, ORANJE, LAND, ACHTERGROND, INKT = (42, 120, 214), (237, 161, 0), "#f0efec", "#fcfcfb", "#0b0b0b"
X0, X1, Y0, Y1 = 0, 280000, 300000, 625000
SCH = 1 / 400  # pixels per meter: een pixel is 4 bij 4 cellen van 100 m
JAREN = (2012, 2017, 2022)


def main(map_):
    map_ = pathlib.Path(map_)
    k = pd.read_csv(map_ / "Bouwterrein_kaart_100m.csv")
    k.columns = [c.lower() for c in k.columns]
    o = pd.read_csv(map_ / "Bouwterrein_overlay_BBG.csv")
    o.columns = [c.lower() for c in o.columns]
    som = k.groupby("jaar")[["ha_nabij", "ha_zonder"]].sum()
    som["raster"] = o.set_index("jaar")["ha_raster"]
    print(som.round(1))

    b, h = int((X1 - X0) * SCH), int((Y1 - Y0) * SCH)
    font = ImageFont.truetype("C:/Windows/Fonts/seguisb.ttf", 30)
    klein = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
    sel = [j for j in sorted(k["jaar"].unique()) if j in JAREN]
    legenda = 60
    img = Image.new("RGB", (b * len(sel) + 20 * (len(sel) - 1), h + 50 + legenda), ACHTERGROND)
    teken = ImageDraw.Draw(img)
    for n, j in enumerate(sel):
        d = k[k["jaar"] == j]
        laag = Image.new("RGB", (b, h), LAND)
        px = laag.load()
        for x, y, a, z in zip(d["x"], d["y"], d["ha_nabij"], d["ha_zonder"]):
            i, r = int((x - X0) * SCH), int((Y1 - y) * SCH)
            if 0 <= i < b and 0 <= r < h and px[i, r] != BLAUW:
                px[i, r] = BLAUW if a >= z else ORANJE
        img.paste(laag, (n * (b + 20), 50))
        teken.text((n * (b + 20) + 10, 5), str(j), font=font, fill=INKT)

    y = h + 50 + 18
    x = 10
    for kleur, tekst in [(BLAUW, "bouwterrein binnen 100 m van een pand in de pijplijn"),
                         (ORANJE, "bouwterrein zonder pand in de pijplijn binnen 100 m")]:
        teken.rectangle([x, y, x + 26, y + 26], fill=kleur)
        teken.text((x + 36, y - 4), tekst, font=klein, fill=INKT)
        x += 36 + int(teken.textlength(tekst, font=klein)) + 40
    uit = map_ / "Bouwterrein_kaart.png"
    img.save(uit)
    print(uit, img.size)


if __name__ == "__main__":
    main(sys.argv[1])
