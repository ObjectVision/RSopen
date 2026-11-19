"""Zet de figuren en tabellen van de ESB-analyses in een Word-document, als intern dossier voor het
gesprek met de VU over het artikel. Alleen presentatie: elk getal komt uit de csv's die GeoDMS schrijft
(ESB_Ruimte/*) of uit de figuren van figuren.py; geen getal staat hier met de hand.

Gebruik: python dossier.py <map A en B> <map G> <map 13> <map D> <map E> <uitvoer.docx>
Een map van een analyse die er nog niet is, geeft in het document de melding dat die volgt.
"""
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from figuren import SECTOREN, lees, nl

GRIJS = RGBColor(0x52, 0x51, 0x4E)


class Dossier:
    def __init__(self):
        self.doc = Document()
        st = self.doc.styles["Normal"]
        st.font.name, st.font.size = "Calibri", Pt(11)
        for s in self.doc.sections:
            s.left_margin = s.right_margin = Cm(2.2)
        self.n_fig = self.n_tab = 0

    def kop(self, tekst, niveau=1):
        self.doc.add_heading(tekst, niveau)

    def alinea(self, tekst):
        return self.doc.add_paragraph(tekst)

    def opsomming(self, regels):
        for r in regels:
            self.doc.add_paragraph(r, style="List Bullet")

    def bijschrift(self, tekst):
        p = self.doc.add_paragraph()
        run = p.add_run(tekst)
        run.font.size, run.font.color.rgb, run.italic = Pt(9.5), GRIJS, True

    def figuur(self, pad, titel, onderschrift="", breedte=14.5):
        pad = Path(pad)
        if not pad.exists():
            self.alinea(f"[Figuur ontbreekt: {pad.name}]")
            return
        self.n_fig += 1
        p = self.doc.add_paragraph()
        p.add_run(f"Figuur {self.n_fig}. {titel}").bold = True
        self.doc.add_picture(str(pad), width=Cm(breedte))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if onderschrift:
            self.bijschrift(onderschrift)

    def tabel(self, kolommen, rijen, titel, onderschrift=""):
        self.n_tab += 1
        p = self.doc.add_paragraph()
        p.add_run(f"Tabel {self.n_tab}. {titel}").bold = True
        t = self.doc.add_table(rows=1, cols=len(kolommen))
        t.style, t.alignment = "Light Grid Accent 1", WD_TABLE_ALIGNMENT.CENTER
        for c, k in zip(t.rows[0].cells, kolommen):
            c.text = k
        for r in rijen:
            cellen = t.add_row().cells
            for i, (c, v) in enumerate(zip(cellen, r)):
                c.text = str(v)
                if i > 0:
                    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for rij in t.rows:
            for c in rij.cells:
                for run in c.paragraphs[0].runs:
                    run.font.size = Pt(9.5)
        if onderschrift:
            self.bijschrift(onderschrift)
        else:
            self.doc.add_paragraph()


def pct(x, dec=0):
    return nl(100 * x, dec) + "%"


def deel_a(d, map_):
    werk = lees(map_ / "WerkenPerBaan_reeks.csv")
    ontl = lees(map_ / "WerkenPerBaan_ontleding.csv").set_index("sector")
    jaren_lisa = werk[werk.m2_per_baan.notna()].jaar
    eind = int(jaren_lisa.max())
    m2 = werk.pivot(index="sector", columns="jaar", values="m2_per_baan")
    banen = werk.pivot(index="sector", columns="jaar", values="banen")
    voet = werk.pivot(index="sector", columns="jaar", values="voetafdruk_m2")
    laatste_bag = int(werk[werk.voetafdruk_m2.notna()].jaar.max())

    d.kop("1. Hoeveel ruimte een baan inneemt (A)")
    d.alinea(
        "De pandvoetafdruk komt uit de BAG op 1 januari van elk jaar. Een pand met verblijfsobjecten voor meer "
        "functies verdeelt zijn voetafdruk over die functies naar hun aandeel in het vloeroppervlak; een pand dat "
        "RSopen als logistiek typeert gaat helemaal naar logistiek. Panden zonder verblijfsobject, zoals schuren en "
        "bijgebouwen, tellen niet mee. De functies gaan naar de zes werksectoren van RSopen. De banen komen uit LISA "
        f"en lopen tot en met {eind}; de BAG loopt tot {laatste_bag}.")
    d.figuur(map_ / "ESB_A1_m2_per_baan.png", "Pandvoetafdruk per baan per sector")
    rijen = []
    for s, lab in SECTOREN.items():
        rijen.append([lab, nl(m2.loc[s, 2012], 1), nl(m2.loc[s, 2019], 1), nl(m2.loc[s, eind], 1),
                      nl(banen.loc[s, eind] / 1000), nl(voet.loc[s, eind] / 1e6, 1)])
    rijen.append(["Zes sectoren samen", nl(voet[2012].sum() / banen[2012].sum(), 1),
                  nl(voet[2019].sum() / banen[2019].sum(), 1), nl(voet[eind].sum() / banen[eind].sum(), 1),
                  nl(banen[eind].sum() / 1000), nl(voet[eind].sum() / 1e6, 1)])
    d.tabel(["Sector", "m² per baan 2012", "2019", str(eind), f"banen {eind} (×1000)", f"voetafdruk {eind} (km²)"],
            rijen, "Voetafdruk per baan, banen en voetafdruk per sector",
            "Bron: BAG (Kadaster), LISA; bewerking in RSopen, ESB_Ruimte/WerkenPerBaan.")
    d.figuur(map_ / "ESB_A3_voetafdruk.png", "Pandvoetafdruk per sector")
    d.figuur(map_ / "ESB_A2_banen.png", "Banen per sector, LISA")

    d.alinea(
        f"Hoeveel van de groei van de voetafdruk tussen 2012 en {eind} komt door meer banen en hoeveel door meer "
        "ruimte per baan? De ontleding is logaritmisch: het deel door de banen is de groei maal het aandeel van de "
        "groei van de banen in de groei van de voetafdruk, beide als logaritme; de twee delen tellen op tot de groei.")
    rijen = []
    for s, lab in SECTOREN.items():
        r = ontl.loc[s]
        rijen.append([lab, nl(r.groei_m2 / 1e6, 1), nl(r.door_banen_m2 / 1e6, 1), nl(r.door_m2baan_m2 / 1e6, 1)])
    som = ontl.loc[list(SECTOREN)].sum()
    rijen.append(["Zes sectoren samen", nl(som.groei_m2 / 1e6, 1), nl(som.door_banen_m2 / 1e6, 1),
                  nl(som.door_m2baan_m2 / 1e6, 1)])
    d.tabel(["Sector", "groei voetafdruk (km²)", "door meer banen", "door m² per baan"], rijen,
            f"Groei van de voetafdruk 2012–{eind} ontleed")
    d.figuur(map_ / "ESB_A4_ontleding.png", f"Groei van de voetafdruk 2012–{eind} ontleed")


def deel_b(d, map_, cbs):
    w = lees(map_ / "WaardePerM2_reeks.csv")
    jaar, begin = int(w.jaar.max()), int(w.jaar.min())
    nu = w[w.jaar == jaar].set_index("sector")
    oud = w[w.jaar == begin].set_index("sector")
    takken = pd.read_csv(cbs, sep=";")
    totaal = takken[takken.Jaar == jaar].BTW_mln.sum() * 1e6

    d.kop("2. Toegevoegde waarde per m² (B)")
    d.alinea(
        "De bruto toegevoegde waarde per bedrijfstak komt uit CBS StatLine 85867NED, op het fijnste niveau dat voor "
        f"elk jaar van {begin} tot en met {jaar} compleet is, zonder de toegerekende huur van eigen woningen. Een "
        "bedrijfstak heeft vaak banen in meer dan een sector; zijn waarde gaat naar de sectoren naar hun aandeel in "
        "de LISA-banen van die tak. Gedeeld door de voetafdruk en de banen uit deel 1 geeft dat de waarde per m² en "
        f"per baan. De zes sectoren dragen samen {pct(nu.btw_euro.sum() / totaal)} van de toegevoegde waarde van alle "
        f"takken in {jaar}; de rest is landbouw en waarde van takken of banen zonder sector.")
    d.figuur(map_ / "ESB_B1_euro_per_m2.png", f"Toegevoegde waarde per m² voetafdruk, {jaar}")
    d.figuur(map_ / "ESB_B2_euro_per_baan.png", f"Toegevoegde waarde per baan, {jaar}")
    rijen = []
    for s, lab in SECTOREN.items():
        r, o = nu.loc[s], oud.loc[s]
        rijen.append([lab, nl(r.btw_euro / 1e9, 1), nl(r.euro_per_m2), nl(r.euro_per_baan / 1000),
                      pct(r.euro2021_per_m2 / o.euro2021_per_m2 - 1), pct(r.euro2021_per_baan / o.euro2021_per_baan - 1)])
    d.tabel(["Sector", f"waarde {jaar} (mld euro)", "euro per m²", "euro per baan (×1000)",
             f"groei per m² {begin}–{jaar}", "groei per baan"], rijen,
            "Toegevoegde waarde per sector, per m² voetafdruk en per baan",
            "Waarde en waarde per m² en per baan in werkelijke prijzen van dat jaar; de groei in prijsniveau 2021, "
            "dus zonder de prijsstijging. Bron: CBS 85867NED, BAG, LISA; ESB_Ruimte/WaardePerM2.")
    d.alinea(
        "Voor een vergelijking tussen sectoren in een jaar maakt het niet uit in welke prijzen je rekent. Voor de "
        "trend wel: in werkelijke prijzen telt de inflatie mee. De volgende figuur is daarom in prijsniveau 2021. Die "
        "reeks van het CBS is een kettingindex en daardoor niet precies optelbaar over takken; vlak bij 2021 is dat "
        "verschil klein.")
    d.figuur(map_ / "ESB_B3_index_m2.png", "Toegevoegde waarde per m² voetafdruk in prijsniveau 2021",
             "De dip in 2020 en 2021 is waarschijnlijk de coronacrisis, die horeca en vervoer het hardst raakte.")


TERMEN_C = ["ln UAI", "ln reistijd OV-knooppunt (2026)", "ln reistijd 500.000 inwoners (2024)",
            "ln afstand op- en afrit", "op een andere IBIS-werklocatie", "in het vaste zeehavengebied", "ln grondprijs",
            "aandeel overig bebouwd 1 km"]
SECTOR_C = dict(zip(["nijverheid", "logistiek", "detailhandel", "overige consumentendiensten",
                     "zakelijke dienstverlening", "overheid en kwartaire diensten"], SECTOREN.values()))


def deel_c(d, map_):
    c = pd.read_csv(map_ / "C_coefficienten_708.csv")
    c["cel"] = c.apply(lambda r: f"{nl(r.coef, 3)} ({nl(r.se, 3)})"
                       + ("" if abs(r.coef) > 1.96 * r.se else " ns"), axis=1)
    tab = c.pivot(index="term", columns="sector", values="cel")

    d.kop("3. Waar sectoren zich vestigen (C)")
    d.alinea(
        "Uit de herschatting van de geschiktheid voor werken in RSopen (ObjectVision/RSopen#708, november 2026): een "
        "multinomiale logit op de bouw van werkpanden van 2017 tot 2022 per cel van 100 m, getoetst op de bouw van "
        "2022 tot 2026. Een positieve coëfficiënt maakt een cel aantrekkelijker; bij een afstand of reistijd betekent "
        "een negatieve coëfficiënt dat de sector de nabijheid zoekt. De tabel toont de termen die voor de vraag naar "
        "verdringing tussen sectoren het meest zeggen; de volledige tabel staat in de bijlage.")
    rijen = [[t] + [tab.loc[t, s] for s in SECTOR_C] for t in TERMEN_C]
    d.tabel(["Term"] + list(SECTOR_C.values()), rijen, "Coëfficiënten van de locatiekeuze per sector (selectie)",
            "Standaardfout geclusterd per pand tussen haakjes; ns is niet significant op 5 procent. "
            "Bron: ObjectVision/RSopen#708, comment van 17 november 2026.")
    return tab


def bijlage_c(d, tab):
    d.kop("Bijlage. Alle coëfficiënten van de herschatting", 1)
    rijen = [[t] + [tab.loc[t, s] for s in SECTOR_C] for t in tab.index]
    d.tabel(["Term"] + list(SECTOR_C.values()), rijen, "Alle coëfficiënten van de locatiekeuze per sector",
            "Standaardfout geclusterd per pand tussen haakjes; ns is niet significant op 5 procent.")


def deel_g(d, map_):
    pijp = lees(map_ / "Bouwterrein_pijplijn_totaal.csv").set_index("jaar")
    bbg = lees(map_ / "Bouwterrein_overlay_BBG.csv").set_index("jaar")

    d.kop("7. Bouwterrein en de pijplijn van de BAG (G)")
    d.alinea(
        "De pijplijn is wat op 1 januari in de BAG vergund of in aanbouw is en nog niet in gebruik: panden met de "
        "status bouwvergunning verleend of bouw gestart. Een pand waarvan die status meer dan vijf jaar oud is, telt "
        "niet mee, want zo'n vergunning wordt vaak nooit gebouwd; zo neemt het model de pijplijn ook. Bouwterrein "
        "komt uit het Bestand Bodemgebruik van het CBS. Een cel van 25 m bouwterrein telt als nabij als het "
        "zwaartepunt van een pand uit de pijplijn binnen 100 m ligt; de rest is bouwterrein zonder zichtbaar "
        "bouwproject in de BAG.")
    d.figuur(map_ / "Bouwterrein_figuur.png", "Woningen en voetafdruk in de pijplijn, en BBG-bouwterrein", breedte=12)
    rijen = []
    for j in pijp.index:
        r = [str(j), nl(pijp.loc[j, "woningen_recent"]), nl(pijp.loc[j, "footprint_recent"] / 1e4)]
        if j in bbg.index:
            b = bbg.loc[j]
            r += [nl(b.ha_raster), pct(b.ha_nabij_recent / b.ha_raster)]
        else:
            r += ["", ""]
        rijen.append(r)
    d.tabel(["1 januari", "woningen in de pijplijn", "voetafdruk pijplijn (ha)", "BBG-bouwterrein (ha)",
             "deel binnen 100 m van de pijplijn"], rijen, "De pijplijn en het bouwterrein",
            "Pijplijn: vergunning hooguit vijf jaar oud. BBG-jaar X naast de BAG van 1 januari X; tussen BBG 2017 "
            "en NBBG 2020 zit een methodebreuk. Bron: BAG (Kadaster), BBG en NBBG (CBS); ESB_Ruimte/Bouwterrein.")
    d.figuur(map_ / "Bouwterrein_kaart.png", "Bouwterrein binnen 100 m van de pijplijn (blauw) en zonder (oranje)",
             "De lange oranje lijnen zijn waarschijnlijk werken aan wegen en dijken die de BBG als bouwterrein "
             "telt, zoals de Afsluitdijk in 2022.")


def volgt(d, kop, tekst):
    d.kop(kop)
    d.alinea(tekst)


def kern(d, map_ab, map_g):
    """Wat opvalt, met elk getal uit de csv's."""
    werk = lees(map_ab / "WerkenPerBaan_reeks.csv")
    eind = int(werk[werk.m2_per_baan.notna()].jaar.max())
    m2 = werk[werk.jaar == eind].set_index("sector").m2_per_baan
    ontl = lees(map_ab / "WerkenPerBaan_ontleding.csv").set_index("sector").loc[list(SECTOREN)]
    w = lees(map_ab / "WaardePerM2_reeks.csv")
    jaar, begin = int(w.jaar.max()), int(w.jaar.min())
    nu, oud = w[w.jaar == jaar].set_index("sector"), w[w.jaar == begin].set_index("sector")
    groei_reeel = nu.euro2021_per_m2 / oud.euro2021_per_m2 - 1
    pijp = lees(map_g / "Bouwterrein_pijplijn_totaal.csv").set_index("jaar")
    bbg = lees(map_g / "Bouwterrein_overlay_BBG.csv").set_index("jaar")
    nabij = bbg.ha_nabij_recent / bbg.ha_raster
    nl_log = ontl.loc[["Nijverheid", "Logistiek"]].groei_m2.sum()
    plus = [SECTOREN[s].lower() for s in ontl.index if ontl.loc[s, "door_m2baan_m2"] > 0]
    meer = ", ".join(plus[:-1]) + " en " + plus[-1]

    d.kop("Wat opvalt")
    d.opsomming([
        f"Een baan in de logistiek neemt in {eind} {nl(m2.Logistiek, 0)} m² pandvoetafdruk in, een baan in de "
        f"zakelijke dienstverlening {nl(m2.Zak_dienstverlening, 0)} m², "
        f"{nl(m2.Logistiek / m2.Zak_dienstverlening, 1)} keer zo weinig. Nijverheid zit op {nl(m2.Nijverheid, 0)} m².",
        f"Per m² voetafdruk levert de zakelijke dienstverlening in {jaar} {nl(nu.euro_per_m2.Zak_dienstverlening)} euro "
        f"toegevoegde waarde op, de logistiek {nl(nu.euro_per_m2.Logistiek)} euro en de nijverheid "
        f"{nl(nu.euro_per_m2.Nijverheid)} euro.",
        f"De voetafdruk van de zes sectoren groeide van 2012 tot {eind} met {nl(ontl.groei_m2.sum() / 1e6)} km², "
        f"waarvan {pct(nl_log / ontl.groei_m2.sum())} bij nijverheid en logistiek. Van de groei komt "
        f"{pct(ontl.door_banen_m2.sum() / ontl.groei_m2.sum())} door meer banen en de rest door meer ruimte per baan; "
        f"meer ruimte per baan is er alleen in {meer}.",
        f"In prijzen van 2021 veranderde de toegevoegde waarde per m² van {begin} tot {jaar} per sector tussen "
        f"{pct(groei_reeel.min())} ({SECTOREN[groei_reeel.idxmin()].lower()}) en {pct(groei_reeel.max())} "
        f"({SECTOREN[groei_reeel.idxmax()].lower()}).",
        "De locatiekeuze verschilt per sector (deel 3): logistiek en nijverheid zoeken IBIS-terreinen en de nabijheid "
        "van een op- en afrit, logistiek mijdt plekken met veel voorzieningen; zakelijke dienstverlening en overheid "
        "zoeken voorzieningen en een OV-knooppunt. Dat wijst op weinig overlap in de plekken die ze zoeken.",
        f"Op 1 januari {int(pijp.index.max())} zitten {nl(pijp.woningen_recent.iloc[-1])} woningen in de pijplijn van "
        f"de BAG. Van het bouwterrein van het CBS ligt {pct(nabij.min())} tot {pct(nabij.max())} binnen 100 m van een "
        "pand uit de pijplijn; de rest heeft geen zichtbaar bouwproject.",
    ])


def main(map_ab, map_g, map_13, map_d, map_e, uit):
    map_ab, map_g = Path(map_ab), Path(map_g)
    cbs = Path(__file__).resolve().parents[3] / "data" / "CBS_85867NED" / "Toegevoegde_waarde_bedrijfstak.csv"
    d = Dossier()
    d.doc.add_heading("Ruimte voor werken: cijfers voor het ESB-artikel", 0)
    d.alinea("Intern werkdocument van Object Vision voor het overleg met de VU, 20 november 2026. Niet verspreiden: "
             "de cijfers zijn nog niet getoetst door anderen.")
    d.alinea(
        "Dit dossier zet de analyses op een rij die we uit de data van RSopen kunnen maken voor de vraag van de "
        "ESB-redactie: zitten laagproductieve sectoren hoogproductieve ruimtelijk in de weg? Alles is landelijk en "
        "gerekend in GeoDMS op de tak esb-ruimte van RSopen (cfg/main/ESB_Ruimte), zodat het na te rekenen is. "
        "Per deel staat de bron onder de tabel.")
    kern(d, map_ab, map_g)
    deel_a(d, map_ab)
    deel_b(d, map_ab, cbs)
    tab_c = deel_c(d, map_ab)
    volgt(d, "4. Vergelijking met figuur 7 van Ruimte voor werken (2022)", "Volgt.")
    volgt(d, "5. Waar de sectoren nu zitten (D)", "Volgt.")
    volgt(d, "6. Werk dat wonen werd (E)", "Volgt.")
    deel_g(d, map_g)
    bijlage_c(d, tab_c)
    d.doc.save(uit)
    print("dossier:", uit)


if __name__ == "__main__":
    main(*sys.argv[1:7])
