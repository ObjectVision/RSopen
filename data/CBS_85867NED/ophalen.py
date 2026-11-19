"""Haalt de bruto toegevoegde waarde in basisprijzen per bedrijfstak op uit CBS StatLine 85867NED
(Productie- en inkomenscomponenten bbp; bedrijfstak; nationale rekeningen) en schrijft een csv die
cfg/main/ESB_Ruimte/WaardePerM2.dms leest.

De csv bevat een indeling van alle economische activiteiten in bedrijfstakken die elkaar niet
overlappen: per tak de fijnste uitsplitsing die voor elk jaar van EERSTE_JAAR tot en met LAATSTE_JAAR
een waarde heeft. De toegerekende huurwaarde van eigen woningen (68A) valt eruit, want daar hoort
geen bedrijfspand bij. Elke tak krijgt het bereik van tweecijferige SBI-afdelingen waar hij over gaat.

Gebruik: python ophalen.py   (schrijft Toegevoegde_waarde_bedrijfstak.csv en SBI2_naar_bedrijfstak.csv,
de koppeling van elke tweecijferige SBI-afdeling aan zijn tak, naast dit script)
"""
import csv
import json
import os
import re
import urllib.request

TABEL = "85867NED"
EERSTE_JAAR = 2012
LAATSTE_JAAR = 2025
BASIS = f"https://opendata.cbs.nl/ODataApi/odata/{TABEL}"
UIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Toegevoegde_waarde_bedrijfstak.csv")
UIT_SBI2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SBI2_naar_bedrijfstak.csv")

# De secties van de SBI als bereik van afdelingen.
SECTIES = {
    "A": (1, 3), "B": (6, 9), "C": (10, 33), "D": (35, 35), "E": (36, 39), "F": (41, 43),
    "G": (45, 47), "H": (49, 53), "I": (55, 56), "J": (58, 63), "K": (64, 66), "L": (68, 68),
    "M": (69, 75), "N": (77, 82), "O": (84, 84), "P": (85, 85), "Q": (86, 88), "R": (90, 93),
    "S": (94, 96), "T": (97, 98), "U": (99, 99),
}


def haal(pad):
    with urllib.request.urlopen(f"{BASIS}/{pad}", timeout=120) as r:
        return json.load(r)["value"]


def bereik(titel):
    """Het bereik van afdelingen van een tak uit zijn titel, of None als de titel er geen noemt."""
    kop = titel.split(" ")[0]
    m = re.fullmatch(r"(\d\d)(?:-(\d\d))?", kop)
    if m:
        return int(m.group(1)), int(m.group(2) or m.group(1))
    m = re.fullmatch(r"([A-U])(?:-([A-U]))?", kop)
    if m:
        return SECTIES[m.group(1)][0], SECTIES[m.group(2) or m.group(1)][1]
    return None


def main():
    takken = haal("BedrijfstakkenBranchesSBI2008?$format=json&$select=Key,Title")
    waarden = haal("TypedDataSet?$format=json&$select=BedrijfstakkenBranchesSBI2008,Perioden,BrutoToegevoegdeWaardeBasisprijzen_3")
    jaren = list(range(EERSTE_JAAR, LAATSTE_JAAR + 1))
    btw = {}
    for r in waarden:
        if r["Perioden"].endswith("JJ00"):
            btw[(r["BedrijfstakkenBranchesSBI2008"].strip(), int(r["Perioden"][:4]))] = r["BrutoToegevoegdeWaardeBasisprijzen_3"]

    knopen = []
    for t in takken:
        b = bereik(t["Title"].strip())
        if b is not None:
            knopen.append({"code": t["Key"].strip(), "titel": t["Title"].strip(), "van": b[0], "tot": b[1]})
    compleet = lambda k: all(btw.get((k["code"], j)) is not None for j in jaren)

    def kinderen(k):
        """De grootste takken binnen k die elkaar niet overlappen, zonder k zelf."""
        binnen = [c for c in knopen if c is not k and k["van"] <= c["van"] and c["tot"] <= k["tot"] and (c["van"], c["tot"]) != (k["van"], k["tot"])]
        top = [c for c in binnen if not any(o is not c and o["van"] <= c["van"] and c["tot"] <= o["tot"] and (o["van"], o["tot"]) != (c["van"], c["tot"]) for o in binnen)]
        return sorted(top, key=lambda c: c["van"])

    def fijnst(k):
        ks = kinderen(k)
        dekt = ks and sum(c["tot"] - c["van"] + 1 for c in ks) == k["tot"] - k["van"] + 1
        if dekt and all(compleet(c) for c in ks):
            return [x for c in ks for x in fijnst(c)]
        return [k]

    secties = [k for k in knopen if re.fullmatch(r"[A-U]", k["titel"].split(" ")[0])]
    indeling = [x for s in secties for x in fijnst(s)]
    # L (68) bevat de toegerekende huurwaarde van eigen woningen; neem alleen 68B, de exploitatie van onroerend goed.
    l68 = {t["Key"].strip(): t["Title"].strip() for t in takken}
    indeling = [x for x in indeling if x["van"] != 68]
    indeling.append({"code": "B000084", "titel": l68["B000084"], "van": 68, "tot": 68})
    indeling.sort(key=lambda x: x["van"])

    gedekt = sorted(a for x in indeling for a in range(x["van"], x["tot"] + 1))
    assert len(gedekt) == len(set(gedekt)), "takken overlappen"
    with open(UIT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Code", "Titel", "SBI2_van", "SBI2_tot", "Jaar", "BTW_mln"])
        for x in indeling:
            for j in jaren:
                v = btw.get((x["code"], j))
                w.writerow([x["code"], x["titel"], x["van"], x["tot"], j, "" if v is None else v])
    with open(UIT_SBI2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["SBI2", "Code"])
        for x in indeling:
            for a in range(x["van"], x["tot"] + 1):
                w.writerow([f"{a:02d}", x["code"]])
    print(f"{len(indeling)} takken, {len(jaren)} jaren, naar {UIT} en {UIT_SBI2}")


if __name__ == "__main__":
    main()
