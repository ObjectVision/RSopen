"""Zet de data achter de kernfiguren voor het ESB-artikel in een Excel. De tabbladen Bron_* bevatten de uitvoer van
GeoDMS (ESB_Ruimte/*) zoals hij is, in m², euro en hectare. De tabellen bij de figuren rekenen daar met Excel-formules
uit, zodat de berekening in de Excel te volgen is: de voetafdruk per baan, de ontleding van de groei, de waarde per
baan en per m², de verdeling over IBIS en de UAI-klassen, de afstand van het bouwterrein tot de pijplijn en wat het
bouwterrein van 2012 later werd. Bij elke tabel staat een Excel-grafiek als begin.

Gebruik: python excel.py <map A en B> <map G> <map D> <uitvoer.xlsx>
De mappen zijn die van WerkenPerBaan en WaardePerM2, van Bouwterrein en van IbisTerreinen, zoals bij dossier.py.
"""
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

from figuren import KLEUR, SECTOREN, lees

GRIJS = "52514E"
KOP_BRON = PatternFill("solid", fgColor="DCE6F2")
KOP_FORMULE = PatternFill("solid", fgColor="E2EFDA")
INVOER = PatternFill("solid", fgColor="FFF2CC")
BLAUW, ORANJE = KLEUR["Nijverheid"][1:], KLEUR["Logistiek"][1:]
ZES = list(SECTOREN.values())


def kop(ws, rij, kolommen, vulling, kol=1):
    for j, k in enumerate(kolommen):
        c = ws.cell(rij, kol + j, k)
        c.font, c.fill = Font(bold=True), vulling
        c.alignment = Alignment(wrap_text=True, vertical="top")


def noot(ws, rij, tekst, kol=1):
    c = ws.cell(rij, kol, tekst)
    c.font = Font(italic=True, size=9, color=GRIJS)


def titel(ws, rij, tekst):
    ws.cell(rij, 1, tekst).font = Font(bold=True, size=12)


def breedtes(ws, eerste=28, rest=14, n=30):
    ws.column_dimensions["A"].width = eerste
    for j in range(2, n):
        ws.column_dimensions[get_column_letter(j)].width = rest


def bron(wb, naam, df, formaat, tekst, namen):
    """Een brontabel: de uitvoer van GeoDMS als platte getallen. namen koppelt kolommen aan een Excel-naam, zodat de
    formules elders leesbaar blijven, zoals SUMIFS(banen; jaar; 2023; sector; "Logistiek")."""
    ws = wb.create_sheet(naam)
    kop(ws, 1, df.columns, KOP_BRON)
    for i, r in enumerate(df.itertuples(index=False), start=2):
        for j, v in enumerate(r, start=1):
            c = ws.cell(i, j, None if isinstance(v, float) and pd.isna(v) else v)
            if df.columns[j - 1] in formaat:
                c.number_format = formaat[df.columns[j - 1]]
    laatste = len(df) + 1
    noot(ws, laatste + 1, tekst)
    for kolom, excelnaam in namen.items():
        letter = get_column_letter(list(df.columns).index(kolom) + 1)
        wb.defined_names[excelnaam] = DefinedName(excelnaam, attr_text=f"{naam}!${letter}$2:${letter}${laatste}")
    ws.freeze_panes = "A2"
    breedtes(ws, 10, 16)
    return ws


def assen(ch, eenheid=None):
    """Assen zichtbaar; openpyxl verbergt ze anders in nieuwere Excel-versies. De eenheid komt in de titel, want een
    astitel van openpyxl valt over de getallen langs de as. Rechte hoeken; Excel rondt ze anders af."""
    ch.x_axis.delete = ch.y_axis.delete = False
    if eenheid and ch.title is not None:
        run = ch.title.tx.rich.p[0].r[0]
        run.t = f"{run.t} ({eenheid})"
    ch.legend.position = "b"
    ch.legend.overlay = False
    if ch.title is not None:
        ch.title.overlay = False
    ch.roundedCorners = False
    ch.height, ch.width = 10, 18


def kleur(serie, hexkleur, lijn=False):
    if lijn:
        serie.graphicalProperties.line.solidFill = hexkleur
        serie.graphicalProperties.line.width = 28000
        serie.smooth = False
    else:
        serie.invertIfNegative = False
        serie.graphicalProperties.solidFill = hexkleur
        serie.graphicalProperties.line.solidFill = hexkleur


def staafgrafiek(ws, kolommen, kop_rij, laatste, tekst, eenheid, plek, kleuren, horizontaal=True, gestapeld=False):
    ch = BarChart()
    ch.type = "bar" if horizontaal else "col"
    ch.title = tekst
    if gestapeld:  # True: gestapeld; "procent": gestapeld tot 100%
        ch.grouping, ch.overlap = ("percentStacked" if gestapeld == "procent" else "stacked"), 100
        if gestapeld == "procent":
            ch.y_axis.number_format = "0%"
    for k, kl in zip(kolommen, kleuren):
        ch.add_data(Reference(ws, min_col=k, min_row=kop_rij, max_row=laatste), titles_from_data=True)
        kleur(ch.series[-1], kl)
    ch.set_categories(Reference(ws, min_col=1, min_row=kop_rij + 1, max_row=laatste))
    if horizontaal:  # sectoren van boven naar beneden, de getallenas onderaan
        ch.x_axis.scaling.orientation = "maxMin"
        ch.y_axis.crosses = "max"
        ch.x_axis.tickLblPos = "low"  # sectornamen links, ook bij negatieve staven
    ch.varyColors = False
    assen(ch, eenheid)
    if len(kolommen) == 1:
        ch.legend = None
    ws.add_chart(ch, plek)


def bronnen(wb, werk, waarde, verdeling, bbg, pijplijn, overgang):
    df = werk.merge(waarde[["jaar", "sector", "btw_euro"]], on=["jaar", "sector"], how="left")
    jaar_sector = pd.DataFrame({"jaar": df.jaar, "sector": df.sector.map(SECTOREN), "banen": df.banen,
                                "voetafdruk (m²)": df.voetafdruk_m2, "toegevoegde waarde (euro)": df.btw_euro})
    bron(wb, "Bron_jaar_sector", jaar_sector,
         {"banen": "#,##0", "voetafdruk (m²)": "#,##0", "toegevoegde waarde (euro)": "#,##0"},
         "Banen uit LISA tot en met het laatste LISA-jaar; pandvoetafdruk uit de BAG op 1 januari, verdeeld over de "
         "functies naar hun vloeroppervlak; bruto toegevoegde waarde uit CBS 85867NED in lopende prijzen, naar de "
         "sectoren verdeeld naar hun LISA-banen. ESB_Ruimte/WerkenPerBaan en WaardePerM2.",
         {"jaar": "jaar", "sector": "sector", "banen": "banen", "voetafdruk (m²)": "voetafdruk",
          "toegevoegde waarde (euro)": "waarde"})

    ibis = pd.DataFrame({"indeling": verdeling.indeling, "klasse": verdeling.klasse,
                         "sector": verdeling.sector.map(lambda s: SECTOREN.get(s, s)), "banen": verdeling.banen,
                         "voetafdruk (m²)": verdeling.voetafdruk_m2})
    bron(wb, "Bron_IBIS", ibis, {"banen": "#,##0", "voetafdruk (m²)": "#,##0"},
         "Banen (LISA 2023) en pandvoetafdruk (BAG 1 januari 2023) per sector, op drie manieren ingedeeld. IBIS: op "
         "welk soort IBIS-werklocatie van 2023, of Geen_IBIS. UAI en Reistijd_OV: vijf klassen die elk 20% van alle "
         "banen van de zes sectoren bevatten; UAI K5 zijn de plekken met de meeste voorzieningen in de buurt, "
         "Reistijd_OV K1 de plekken die het dichtst bij een OV-knooppunt liggen. Een pand of vestiging telt op de plek "
         "van zijn zwaartepunt of punt. ESB_Ruimte/IbisTerreinen.",
         {"indeling": "ibis_indeling", "klasse": "ibis_klasse", "sector": "ibis_sector", "banen": "ibis_banen",
          "voetafdruk (m²)": "ibis_voetafdruk"}).column_dimensions["A"].width = 21.7

    b = bbg.set_index("jaar")
    p = pijplijn.set_index("jaar")
    bt = pd.DataFrame({"jaar": b.index, "BBG-bouwterrein (ha)": b.ha_raster.values,
                       "binnen 100 m van de pijplijn (ha)": b.ha_nabij_recent.values,
                       "binnen 250 m van de pijplijn (ha)": b.ha_nabij_recent_ruim.values,
                       "woningen in de pijplijn op 1 januari": p.woningen_recent.reindex(b.index).values})
    bron(wb, "Bron_bouwterrein", bt, {c: "#,##0" for c in bt.columns[1:]},
         "Bouwterrein uit het Bestand Bodemgebruik van het CBS, in cellen van 25 m. Pijplijn: panden met de status "
         "bouwvergunning verleend of bouw gestart op 1 januari, met een vergunning van hooguit vijf jaar oud; de "
         "afstand is die tot het zwaartepunt van zo'n pand. BBG-jaar X naast de BAG van 1 januari X; tussen BBG 2017 "
         "en NBBG 2020 zit een methodebreuk. ESB_Ruimte/Bouwterrein.", {})

    ovg = pd.DataFrame({"reeks": overgang.reeks, "jaar": overgang.jaar, "vorige jaargang": overgang.vorige_jaargang,
                        "klasse": overgang.klasse, "oppervlakte (ha)": overgang.ha})
    bron(wb, "Bron_overgang", ovg, {"oppervlakte (ha)": "#,##0"},
         "Het bouwterrein van de BBG en zijn grondgebruik in latere jaargangen, naar de hoofdklassen van de BBG. Reeks "
         "volgende jaargang: het bouwterrein van de vorige jaargang naar zijn klasse in dit jaar, plus het bouwterrein "
         "dat er in dit jaar nieuw is. Reeks cohort 2012: het bouwterrein van 2012 naar zijn klasse in elk later jaar. "
         "Tot 2017 uit de klasse per vlak in het CBS-mutatiebestand BBG 1996–2017, van 2017 naar 2020 een overlay met "
         "het CBS-mutatiebestand NBBG 2022, en daarna de klasse per vlak in de NBBG. Tussen BBG 2017 en NBBG 2020 zit "
         "een methodebreuk. ESB_Ruimte/Bouwterrein_overgang.py.",
         {"reeks": "ovg_reeks", "jaar": "ovg_jaar", "vorige jaargang": "ovg_vorige", "klasse": "ovg_klasse", "oppervlakte (ha)": "ovg_ha"}
         ).column_dimensions["D"].width = 34
    return jaar_sector, bt


def blad_ruimte_per_baan(wb, jaar_sector):
    """Voetafdruk per baan per jaar en sector, met SUMIFS uit Bron_jaar_sector."""
    jaren = sorted(jaar_sector[jaar_sector.banen.notna() & jaar_sector["voetafdruk (m²)"].notna()].jaar.unique())
    ws = wb.create_sheet("Ruimte_per_baan")
    titel(ws, 1, f"Pandvoetafdruk per baan, {jaren[0]}–{jaren[-1]} (m² per LISA-baan)")
    kop(ws, 2, ["jaar"] + ZES, KOP_FORMULE)
    for i, j in enumerate(jaren, start=3):
        ws.cell(i, 1, int(j))
        for k in range(len(ZES)):
            s = f"{get_column_letter(k + 2)}$2"
            c = ws.cell(i, k + 2, f"=SUMIFS(voetafdruk,jaar,$A{i},sector,{s})/SUMIFS(banen,jaar,$A{i},sector,{s})")
            c.number_format = "#,##0.0"
    laatste = 2 + len(jaren)
    noot(ws, laatste + 1, "Formules uit Bron_jaar_sector; ESB_Ruimte/WerkenPerBaan.")
    ch = LineChart()
    ch.title = "Pandvoetafdruk per baan"
    ch.add_data(Reference(ws, min_col=2, max_col=1 + len(ZES), min_row=2, max_row=laatste), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=3, max_row=laatste))
    for serie, s in zip(ch.series, SECTOREN):
        kleur(serie, KLEUR[s][1:], lijn=True)
    assen(ch, "m² per baan")
    ws.add_chart(ch, "I2")
    breedtes(ws, 8, 13)


def blad_per_sector(wb, begin, eind):
    """Een rij per sector: banen, voetafdruk en waarde uit Bron_jaar_sector, de ontleding van de groei, de waarde per
    baan en per m² en de verdeling over IBIS en UAI uit Bron_IBIS, alles als formule."""
    ws = wb.create_sheet("Per_sector")
    for r, (naam, v) in enumerate([("beginjaar", begin), ("eindjaar", eind)], start=1):
        ws.cell(r, 1, naam).font = Font(bold=True)
        c = ws.cell(r, 2, v)
        c.fill = INVOER
        wb.defined_names[naam] = DefinedName(naam, attr_text=f"Per_sector!$B${r}")
    K = 4  # rij van de kop
    kolommen = [
        ("sector", None, None),
        ('="banen "&beginjaar', "#,##0", 'SUMIFS(banen,jaar,beginjaar,sector,$A{r})'),
        ('="banen "&eindjaar', "#,##0", 'SUMIFS(banen,jaar,eindjaar,sector,$A{r})'),
        ('="voetafdruk "&beginjaar&" (km²)"', "#,##0.0", 'SUMIFS(voetafdruk,jaar,beginjaar,sector,$A{r})/1000000'),
        ('="voetafdruk "&eindjaar&" (km²)"', "#,##0.0", 'SUMIFS(voetafdruk,jaar,eindjaar,sector,$A{r})/1000000'),
        ('="m² per baan "&beginjaar', "#,##0.0", '$D{r}*1000000/$B{r}'),
        ('="m² per baan "&eindjaar', "#,##0.0", '$E{r}*1000000/$C{r}'),
        ("groei voetafdruk (km²)", "#,##0.0", '$E{r}-$D{r}'),
        ("door meer banen (km²)", "#,##0.0", '$H{r}*LN($C{r}/$B{r})/LN($E{r}/$D{r})'),
        ("door m² per baan (km²)", "#,##0.0", '$H{r}-$I{r}'),
        ('="toegevoegde waarde "&eindjaar&" (mld euro)"', "#,##0.0",
         'SUMIFS(waarde,jaar,eindjaar,sector,$A{r})/10^9'),
        ("euro per baan", "#,##0", '$K{r}*10^9/$C{r}'),
        ("euro per m²", "#,##0", '$K{r}*10^9/($E{r}*10^6)'),
        ("per baan, zes sectoren = 100", "0", '100*$L{r}/$L$' + str(K + 7)),
        ("per m², zes sectoren = 100", "0", '100*$M{r}/$M$' + str(K + 7)),
        ("deel banen op IBIS (2023)", "0%",
         '1-SUMIFS(ibis_banen,ibis_indeling,"IBIS",ibis_klasse,"Geen_IBIS",ibis_sector,$A{r})'
         '/SUMIFS(ibis_banen,ibis_indeling,"IBIS",ibis_sector,$A{r})'),
        ("deel banen bij de hoogste UAI (2023)", "0%",
         'SUMIFS(ibis_banen,ibis_indeling,"UAI",ibis_klasse,"K5",ibis_sector,$A{r})'
         '/SUMIFS(ibis_banen,ibis_indeling,"UAI",ibis_sector,$A{r})'),
        ("deel voetafdruk bij de hoogste UAI (2023)", "0%",
         'SUMIFS(ibis_voetafdruk,ibis_indeling,"UAI",ibis_klasse,"K5",ibis_sector,$A{r})'
         '/SUMIFS(ibis_voetafdruk,ibis_indeling,"UAI",ibis_sector,$A{r})'),
    ]
    kop(ws, K, [k[0] for k in kolommen], KOP_FORMULE)
    ws.row_dimensions[K].height = 60
    rijen = ZES + ["Zes sectoren samen"]
    for i, s in enumerate(rijen, start=K + 1):
        ws.cell(i, 1, s)
        for j, (_, fmt, f) in enumerate(kolommen[1:], start=2):
            if s == "Zes sectoren samen":
                # Bedragen, aantallen en de ontleding opgeteld over de sectoren, zoals in dossier.py; de ontleding van
                # het totaal zelf zou ook de verschuiving tussen sectoren meetellen. De verhoudingen zoals in de rijen
                # erboven, en de aandelen uit Bron_IBIS zonder voorwaarde op de sector.
                letter = get_column_letter(j)
                if j in (2, 3, 4, 5, 9, 10, 11):
                    f = f"SUM({letter}{K + 1}:{letter}{K + 6})"
                elif "ibis_sector" in f:
                    f = f.replace(",ibis_sector,$A{r}", "")
            c = ws.cell(i, j, "=" + f.format(r=i))
            c.number_format = fmt
    laatste = K + len(rijen)
    breedtes(ws, 26, 12)
    plek = laatste + 4
    staafgrafiek(ws, [9, 10], K, laatste - 1, "Groei van de voetafdruk ontleed", "km²", f"A{plek}", [BLAUW, ORANJE])
    staafgrafiek(ws, [14, 15], K, laatste - 1, "Toegevoegde waarde per baan en per m²", "zes sectoren = 100",
                 f"J{plek}", [BLAUW, ORANJE])
    staafgrafiek(ws, [16, 17], K, laatste, "Waar de banen zitten, 2023", "deel van de banen van de sector",
                 f"A{plek + 22}", [BLAUW, ORANJE])


def blad_bouwterrein(wb, n):
    """Het bouwterrein naar de afstand tot de pijplijn, met formules uit Bron_bouwterrein."""
    ws = wb.create_sheet("Bouwterrein")
    titel(ws, 1, "Bouwterrein naar de afstand tot een bouwproject in de BAG")
    kolommen = [("jaar", "0", "Bron_bouwterrein!A{b}"),
                ("binnen 100 m van de pijplijn (ha)", "#,##0", "Bron_bouwterrein!C{b}"),
                ("100 tot 250 m (ha)", "#,##0", "Bron_bouwterrein!D{b}-Bron_bouwterrein!C{b}"),
                ("verder dan 250 m (ha)", "#,##0", "Bron_bouwterrein!B{b}-Bron_bouwterrein!D{b}"),
                ("BBG-bouwterrein (ha)", "#,##0", "SUM(B{r}:D{r})"),
                ("deel binnen 100 m", "0%", "B{r}/E{r}"),
                ("deel binnen 250 m", "0%", "(B{r}+C{r})/E{r}"),
                ("woningen in de pijplijn op 1 januari", "#,##0", "Bron_bouwterrein!E{b}")]
    kop(ws, 2, [k[0] for k in kolommen], KOP_FORMULE)
    ws.row_dimensions[2].height = 45
    for i in range(n):
        r, b = 3 + i, 2 + i
        for j, (_, fmt, f) in enumerate(kolommen, start=1):
            c = ws.cell(r, j, "=" + f.format(r=r, b=b))
            c.number_format = fmt
    laatste = 2 + n
    breedtes(ws, 8, 15)
    staafgrafiek(ws, [2, 3, 4], 2, laatste, "Bouwterrein en de pijplijn van de BAG", "ha", f"A{laatste + 4}",
                 [BLAUW, "8FB8EB", "D0CFCB"], horizontaal=False, gestapeld=True)


# De groepen in de grafieken van Bouwterrein_overgang, met hun klassen uit Bron_overgang en hun kleur. Verkeer,
# natuur, water en de kleine klassen vormen samen de rest (None), zodat de grafiek leesbaar blijft.
NAAR = [("wonen", ["Wonen"], ORANJE),
        ("bedrijfsterrein", ["Bedrijfsterrein"], BLAUW),
        ("voorzieningen, detailhandel en horeca", ["Voorzieningen, detailhandel en horeca"], KLEUR["Zak_dienstverlening"][1:]),
        ("park, sport en recreatie", ["Park, sport en recreatie"], KLEUR["Detailhandel"][1:]),
        ("agrarisch", ["Agrarisch"], KLEUR["Ov_consumentendiensten"][1:]),
        ("verkeer, natuur, water en overig", None, "DDDCD7")]
VOORRAAD = [("blijft bouwterrein", ["Bleef bouwterrein"], "52514E")] + NAAR + [("volgende jaargang nog niet bekend", None, "A8A6A0")]
COHORT = [("nog bouwterrein", ["Nog bouwterrein"], "52514E")] + NAAR


def blok(ws, rij, reeks, jaren, groepen, totaal):
    """Een tabel met een rij per jaar en een kolom per groep, met SUMIFS uit Bron_overgang voor de reeks; de rest is
    het totaal van de reeks in dat jaar min de groepen ervoor. Geeft de kolom van het totaal en de laatste rij."""
    n = len(groepen)
    kop(ws, rij, ["jaar"] + [g for g, _, _ in groepen] + [totaal], KOP_FORMULE)
    ws.row_dimensions[rij].height = 45
    tot = get_column_letter(n + 2)
    for i, jaar in enumerate(jaren, start=rij + 1):
        ws.cell(i, 1, int(jaar))
        for j, (_, klassen, _) in enumerate(groepen, start=2):
            if klassen is None:
                f = f"={tot}{i}-SUM(B{i}:{get_column_letter(j - 1)}{i})"
            else:
                f = "=" + "+".join(f'SUMIFS(ovg_ha,ovg_reeks,"{reeks}",ovg_jaar,$A{i},ovg_klasse,"{k}")' for k in klassen)
            ws.cell(i, j, f).number_format = "#,##0"
        ws.cell(i, n + 2, f'=SUMIFS(ovg_ha,ovg_reeks,"{reeks}",ovg_jaar,$A{i})').number_format = "#,##0"
    return n + 2, rij + len(jaren)


def blad_overgang(wb, jaren_voorraad, jaren_cohort):
    """Het bouwterrein per BBG-jaargang, verdeeld naar zijn grondgebruik in de volgende jaargang, en daaronder het
    cohort van 2012, in ha met SUMIFS uit Bron_overgang."""
    ws = wb.create_sheet("Bouwterrein_overgang")
    titel(ws, 1, "Bouwterrein per BBG-jaargang, naar zijn grondgebruik in de volgende jaargang (ha)")
    n = len(VOORRAAD)
    tk = n + 2
    tot = get_column_letter(tk)
    kop(ws, 2, ["jaar"] + [g for g, _, _ in VOORRAAD] + ["bouwterrein dit jaar", "volgende jaargang",
                                                         "som overgangen (controle)"], KOP_FORMULE)
    ws.row_dimensions[2].height = 45
    laatste = 2 + len(jaren_voorraad)
    volgende = '"volgende jaargang",ovg_vorige,$A{i}'
    for i, jaar in enumerate(jaren_voorraad, start=3):
        ws.cell(i, 1, int(jaar))
        for j, (g, klassen, _) in enumerate(VOORRAAD, start=2):
            if g == "volgende jaargang nog niet bekend":  # de laatste jaargang heeft nog geen opvolger
                f = f"=IF(COUNTIFS(ovg_reeks,{volgende.format(i=i)})=0,{tot}{i},0)"
            elif klassen is None:  # de rest: de voorraad min de groepen ervoor en het onbekende deel
                f = f"={tot}{i}-SUM(B{i}:{get_column_letter(j - 1)}{i})-{get_column_letter(n + 1)}{i}"
            else:
                f = "=" + "+".join(f'SUMIFS(ovg_ha,ovg_reeks,{volgende.format(i=i)},ovg_klasse,"{k}")' for k in klassen)
            ws.cell(i, j, f).number_format = "#,##0"
        # de voorraad van dit jaar: wat bouwterrein bleef plus wat er nieuw bijkwam sinds de vorige jaargang
        ws.cell(i, tk, '=SUMIFS(ovg_ha,ovg_reeks,"volgende jaargang",ovg_jaar,$A{i},ovg_klasse,"Bleef bouwterrein")'
                       '+SUMIFS(ovg_ha,ovg_reeks,"volgende jaargang",ovg_jaar,$A{i},ovg_klasse,"Nieuw bouwterrein")'
                .replace("{i}", str(i))).number_format = "#,##0"
        ws.cell(i, tk + 1, f'=IFERROR(AVERAGEIFS(ovg_jaar,ovg_reeks,{volgende.format(i=i)}),"")').number_format = "0"
        ws.cell(i, tk + 2, f'=SUMIFS(ovg_ha,ovg_reeks,{volgende.format(i=i)})-SUMIFS(ovg_ha,ovg_reeks,'
                           f'{volgende.format(i=i)},ovg_klasse,"Nieuw bouwterrein")').number_format = "#,##0"
    noot(ws, laatste + 1, "De staaf van een jaar is het bouwterrein in die BBG-jaargang, verdeeld naar wat het in de "
         "volgende jaargang is. De overgang van 2017 naar 2020 loopt over de methodebreuk tussen BBG en NBBG.")
    staafgrafiek(ws, list(range(2, n + 2)), 2, laatste, "Bouwterrein en wat het in de volgende BBG-jaargang is", "ha",
                 f"A{laatste + 3}", [kl for _, _, kl in VOORRAAD], horizontaal=False, gestapeld=True)
    r2 = laatste + 26
    titel(ws, r2 - 1, "Wat werd het bouwterrein van 2012? Grondgebruik in de latere BBG-jaargangen (ha)")
    _, laatste2 = blok(ws, r2, "cohort 2012", jaren_cohort, COHORT, "bouwterrein 2012")
    staafgrafiek(ws, list(range(2, len(COHORT) + 2)), r2, laatste2, "Wat werd het bouwterrein van 2012", "ha",
                 f"A{laatste2 + 3}", [kl for _, _, kl in COHORT], horizontaal=False, gestapeld=True)
    breedtes(ws, 8, 15)


def blad_per_jaar(wb, n):
    """Alle reeksen per jaar en sector, met de verhoudingen als formule uit Bron_jaar_sector."""
    ws = wb.create_sheet("Per_jaar")
    kolommen = [("jaar", "0", "Bron_jaar_sector!A{b}"), ("sector", None, "Bron_jaar_sector!B{b}"),
                ("banen (LISA)", "#,##0", 'IF(Bron_jaar_sector!C{b}="","",Bron_jaar_sector!C{b})'),
                ("voetafdruk (km²)", "#,##0.0", 'IF(Bron_jaar_sector!D{b}="","",Bron_jaar_sector!D{b}/10^6)'),
                ("m² voetafdruk per baan", "#,##0.0", 'IF(OR(C{r}="",D{r}=""),"",D{r}*10^6/C{r})'),
                ("toegevoegde waarde (mld euro)", "#,##0.0",
                 'IF(Bron_jaar_sector!E{b}="","",Bron_jaar_sector!E{b}/10^9)'),
                ("euro per baan", "#,##0", 'IF(F{r}="","",F{r}*10^9/C{r})'),
                ("euro per m²", "#,##0", 'IF(F{r}="","",F{r}*10^9/(D{r}*10^6))')]
    kop(ws, 1, [k[0] for k in kolommen], KOP_FORMULE)
    for i in range(n):
        r = 2 + i
        for j, (_, fmt, f) in enumerate(kolommen, start=1):
            c = ws.cell(r, j, "=" + f.format(r=r, b=r))
            if fmt:
                c.number_format = fmt
    noot(ws, n + 2, "Formules uit Bron_jaar_sector; een lege cel is een jaar zonder LISA, BAG of waarde.")
    ws.freeze_panes = "A2"
    breedtes(ws, 8, 16)
    ws.column_dimensions["B"].width = 26


def main(map_ab, map_g, map_d, uit):
    map_ab, map_g, map_d = Path(map_ab), Path(map_g), Path(map_d)
    werk = lees(map_ab / "WerkenPerBaan_reeks.csv")
    waarde = lees(map_ab / "WaardePerM2_reeks.csv")
    overgang = lees(map_g / "Bouwterrein_overgang_BBG.csv")  # van Bouwterrein_overgang.py
    wb = Workbook()
    eerste = wb.active
    jaar_sector, bt = bronnen(wb, werk, waarde, lees(map_d / "IbisTerreinen_verdeling.csv"),
                              lees(map_g / "Bouwterrein_overlay_BBG.csv"),
                              lees(map_g / "Bouwterrein_pijplijn_totaal.csv"), overgang)
    wb.remove(eerste)
    blad_ruimte_per_baan(wb, jaar_sector)
    eind = int(werk[werk.m2_per_baan.notna()].jaar.max())
    blad_per_sector(wb, 2012, eind)
    blad_bouwterrein(wb, len(bt))
    blad_overgang(wb, sorted(overgang[overgang.reeks == "volgende jaargang"].jaar.unique()),
                  sorted(overgang[overgang.reeks == "cohort 2012"].jaar.unique()))
    blad_per_jaar(wb, len(jaar_sector))
    # de tabellen vooraan, de bronnen erachter
    volgorde = ["Ruimte_per_baan", "Per_sector", "Bouwterrein", "Bouwterrein_overgang", "Per_jaar"]
    for naam in volgorde:
        wb.move_sheet(naam, offset=volgorde.index(naam) - wb.sheetnames.index(naam))
    wb.active = 0
    wb.save(uit)
    print("Excel in", uit)


if __name__ == "__main__":
    main(*sys.argv[1:5])
