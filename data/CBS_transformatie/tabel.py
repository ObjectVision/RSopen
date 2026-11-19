"""Zet de landelijke CBS-reeksen voor transformatie en functiewijziging van woningen in een csv: per tabel en jaar
de toevoeging door transformatie, de late respons transformatie, de toevoeging door functiewijziging en de
onttrekking door functiewijziging."""
import csv
import json
import os
import sys

map_in, uit = sys.argv[1], sys.argv[2]
kolommen = {
    "84903NED": ["Transformatie_6", "LateResponsTransformatie_7", "VanLogiesfunctieNaarWoonfunctie_14",
                 "VanOverigeFunctieNaarWoonfunctie_15", "VanWoonNaarLogiesfunctie_27", "VanWoonfunctieNaarOverigeFunctie_28",
                 "TotaalOverigeToevoegingen_3", "Nieuwbouw_2"],
    "86054NED": ["Transformatie_6", "LateResponsTransformatie_7", "VanLogiesfunctieNaarWoonfunctie_12",
                 "VanOverigeFunctieNaarWoonfunctie_13", "VanWoonNaarLogiesfunctie_23", "VanWoonfunctieNaarOverigeFunctie_24",
                 "TotaalOverigeToevoegingen_3", "Nieuwbouw_2"],
}
namen = ["transformatie", "late_respons_transformatie", "logies_naar_woon", "overig_naar_woon",
         "woon_naar_logies", "woon_naar_overig", "overige_toevoegingen_totaal", "nieuwbouw"]
rijen = []
for tabel, kol in kolommen.items():
    data = json.load(open(os.path.join(map_in, f"{tabel}_data_NL.json"), encoding="utf-8"))
    for d in data:
        per = d["Perioden"]
        if not per.endswith("JJ00"):
            continue
        rijen.append([tabel, int(per[:4])] + [d.get(k) for k in kol])
with open(uit, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["tabel", "jaar"] + namen)
    w.writerows(sorted(rijen, key=lambda r: (r[1], r[0])))
for r in sorted(rijen, key=lambda r: (r[1], r[0])):
    print(r)
