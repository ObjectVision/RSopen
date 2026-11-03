# -*- coding: utf-8 -*-
# Uitstelgewichten voor de sterfte-indicator (#484). Gebruikt door het AdHoc-item SterfteUitgesteld van het resultatenrapport 1.0
# (#828, uit de configuratie sinds de verhuizing van de AdHoc-items); de structurele opvolger, met de horizon uit ExportZichtjaar, staat
# als eigen issue op de agenda.
#
# Een vermeden sterfgeval is een uitgesteld sterfgeval: wie door meer groen dit jaar niet overlijdt, leeft door met de
# overlevingskansen van iemand van die leeftijd. Dit script leidt uit de CBS-periode-overlevingstafel (StatLine 37360ned,
# totaal mannen en vrouwen, hier het jaar 2024, kolommen Sterftekans, Levenden, Overledenen en Levensverwachting per
# leeftijd) drie dingen af:
#   S(k)               de kans dat een uitgesteld sterfgeval k jaar later nog in leven is, gewogen over de leeftijd van
#                      overlijden met de tafeloverledenen d(x): S(k) = som_x d(x) * l(x+k)/l(x) / som_x d(x);
#                      voorbij 99 jaar loopt l(x) exponentieel door met de levensverwachting op 99 jaar;
#   w_InLeven2120      per periode tussen twee zichtjaren het gemiddelde van S(2120 - y) over de jaren y van de periode:
#                      het deel van de in die periode uitgestelde sterfgevallen dat 2120 haalt;
#   w_Levensjaren2120  per periode het gemiddelde van de som van S(k) voor k = 1 tot 2120 - y: de extra levensjaren
#                      binnen de horizon per uitgesteld sterfgeval.
# De som van S(k) over alle k is de verwachte extra levensjaren per uitgesteld sterfgeval zonder horizon; die staat als
# parameter LevensjarenPerUitgesteldSterfgeval in het AdHoc-item. Aannames: de uitgestelde sterfgevallen zijn naar
# leeftijd verdeeld als alle sterfgevallen in de tafel, de kansen van 2024 gelden ook in latere jaren, en na het uitstel
# gelden weer de gewone kansen.
#
# Gebruik: python uitstelgewichten.py CBS_37360ned_2024_totaal.csv uitstelgewichten_2024.csv
import csv, math, sys
rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8'), delimiter=';'))
rows.sort(key=lambda r: int(r['Leeftijd']))
l = [float(r['Levenden']) for r in rows]; dx = [float(r['Overledenen']) for r in rows]; e = [float(r['Levensverwachting']) for r in rows]
n = len(rows); assert n == 100, n
def lv(a):
    return l[a] if a < n else l[n - 1] * math.exp(-(a - (n - 1)) / e[n - 1])
def S(k):
    return sum(dx[x] * lv(x + k) / l[x] for x in range(n)) / sum(dx)
Sk = [S(k) for k in range(0, 130)]
D = sum(Sk[1:])
H = 2120
zichtjaren = [('Y2040', 2023, 2040)] + [('Y%d' % j, j - 10, j) for j in range(2050, H + 10, 10)]
with open(sys.argv[2], 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['Naam', 'Van', 'Tot', 'Jaren', 'w_InLeven2120', 'w_Levensjaren2120'])
    for naam, a, b in zichtjaren:
        jaren = range(a + 1, b + 1)
        w_leven = sum(Sk[H - y] for y in jaren) / len(jaren)
        w_lj = sum(sum(Sk[k] for k in range(1, H - y + 1)) for y in jaren) / len(jaren)
        w.writerow([naam, a, b, len(jaren), '%.6f' % w_leven, '%.6f' % w_lj])
        print('%-6s %4d-%4d %8.4f %8.3f' % (naam, a, b, w_leven, w_lj))
print('levensverwachting bij geboorte %.2f; extra levensjaren per uitgesteld sterfgeval (som S(k)) %.2f' % (e[0], D))